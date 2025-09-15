# 配置 poppler 路径
import os
from pathlib import Path

# 尝试从环境变量获取，否则使用默认路径
poppler_path = os.getenv("POPPLER_PATH")
if not poppler_path:
    # 常见安装路径
    possible_paths = [
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files (x86)\poppler\Library\bin",
        r"E:\Programs\poppler-25.07.0\Library\bin"
    ]
    for path in possible_paths:
        if Path(path).exists():
            poppler_path = path
            break

if not poppler_path:
    raise FileNotFoundError(
        "未找到poppler路径，请设置POPPLER_PATH环境变量或安装poppler到默认位置"
    )

# 临时添加到系统路径
os.environ["PATH"] = poppler_path + os.pathsep + os.environ["PATH"]

# 导入必要的库
import fitz  # PyMuPDF
from fitz import open as fitz_open
from unstructured.partition.pdf import partition_pdf
from langchain_unstructured import UnstructuredLoader
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from PIL import Image

# 设置文件路径
pdfFileName = "1"
pdf_path = f"{pdfFileName}.pdf"
output_dir = pdfFileName
os.makedirs(output_dir, exist_ok=True)

# 方法1: 使用 langchain_unstructured 加载 PDF
def load_with_langchain():
    print("使用 LangChain UnstructuredLoader 加载 PDF...")
    loader_local = UnstructuredLoader(
        file_path=pdf_path,
        strategy="hi_res",  # 高分辨率模式，支持复杂文档
        infer_table_structure=True,  # 自动解析表格结构
        languages=["chi_sim", "eng"],  # 支持中英文 OCR
        ocr_engine="paddleocr",  # 指定 PaddleOCR 作为 OCR 引擎
        poppler_path=poppler_path  # 明确指定 poppler 路径
    )

    docs_local = []
    for doc in loader_local.lazy_load():
        docs_local.append(doc)
    
    print(f"成功加载 {len(docs_local)} 个文档元素")
    return docs_local

# 方法2: 使用 unstructured 直接处理 PDF
def process_with_unstructured():
    print("使用 unstructured 直接处理 PDF...")
    # 提取文本/结构化内容
    elements = partition_pdf(
        filename=pdf_path,
        infer_table_structure=True,  # 开启表格结构检测
        strategy="hi_res",  # 高分辨率 OCR, 适合复杂表格
        languages=["chi_sim", "eng"],  # 中英文混合识别
        ocr_engine="paddleocr",  # 指定 PaddleOCR 引擎
        poppler_path=poppler_path  # 明确指定 poppler 路径
    )
    
    print(f"成功提取 {len(elements)} 个文档元素")
    return elements

# 可视化函数
def plot_pdf_with_boxes(pdf_page, segments):
    pix = pdf_page.get_pixmap()
    pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    fig, ax = plt.subplots(1, figsize=(10, 10))
    ax.imshow(pil_image)
    categories = set()
    category_to_color = {
        "Title": "orchid",
        "Image": "forestgreen",
        "Table": "tomato",
    }
    for segment in segments:
        points = segment["coordinates"]["points"]
        layout_width = segment["coordinates"]["layout_width"]
        layout_height = segment["coordinates"]["layout_height"]
        scaled_points = [
            (x * pix.width / layout_width, y * pix.height / layout_height)
            for x, y in points
        ]
        box_color = category_to_color.get(segment["category"], "deepskyblue")
        categories.add(segment["category"])
        rect = patches.Polygon(
            scaled_points, linewidth=1, edgecolor=box_color, facecolor="none"
        )
        ax.add_patch(rect)

    # Make legend
    legend_handles = [patches.Patch(color="deepskyblue", label="Text")]
    for category in ["Title", "Image", "Table"]:
        if category in categories:
            legend_handles.append(
                patches.Patch(color=category_to_color[category], label=category)
            )
    ax.axis("off")
    ax.legend(handles=legend_handles, loc="upper right")
    plt.tight_layout()
    plt.show()

def render_page(doc_list, page_number=None, print_text=True, save_annotated=False):
    """渲染PDF页面并添加标注
    
    参数:
        doc_list: 文档元素列表(包含metadata)
        page_number: 指定页码(None表示所有页面)
        print_text: 是否打印提取的文本
        save_annotated: 是否保存标注版PDF
    """
    # 打开原始PDF文件
    pdf_doc = fitz_open(pdf_path)
    output_doc = None
    
    if save_annotated:
        output_path = f"{Path(pdf_path).stem}_annotated.pdf"
        output_doc = fitz_open()
    
    pages_to_process = [page_number - 1] if page_number else range(len(pdf_doc))
    
    for page_num in pages_to_process:
        pdf_page = pdf_doc.load_page(page_num)
        current_page = page_num + 1
        page_docs = [
            doc for doc in doc_list 
            if doc.metadata.get("page_number") == current_page
        ]
        segments = [doc.metadata for doc in page_docs]
        
        if not save_annotated:
            plot_pdf_with_boxes(pdf_page, segments)
        
        if save_annotated:
            output_page = output_doc.new_page(
                width=pdf_page.rect.width,
                height=pdf_page.rect.height
            )
            output_page.show_pdf_page(output_page.rect, pdf_doc, page_num)
            
            category_to_color = {
                "Title": (0.6, 0.2, 0.8),   # 紫色
                "Image": (0.0, 0.5, 0.0),    # 绿色
                "Table": (1.0, 0.4, 0.4),   # 红色
                "Text": (0.0, 0.7, 1.0)     # 蓝色
            }
            
            for segment in segments:
                points = segment["coordinates"]["points"]
                layout_width = segment["coordinates"]["layout_width"]
                layout_height = segment["coordinates"]["layout_height"]
                scaled_points = [
                    (x * pdf_page.rect.width / layout_width, 
                     y * pdf_page.rect.height / layout_height)
                    for x, y in points
                ]
                
                # 添加标注
                annot = output_page.add_polygon_annot(scaled_points)
                annot.set_colors(
                    stroke=category_to_color.get(segment["category"], (0.0, 0.7, 1.0))
                )
                annot.set_opacity(0.4)
                annot.update()
                
                # 为重要元素添加标签
                if segment["category"] in ["Title", "Table"]:
                    center_x = sum(p[0] for p in scaled_points)/len(scaled_points)
                    center_y = sum(p[1] for p in scaled_points)/len(scaled_points)
                    output_page.insert_text(
                        (center_x, center_y - 10),
                        segment["category"],
                        fontsize=10,
                        color=(0,0,0),
                        rotate=0
                    )
        
        if print_text:
            print(f"\n=== 第 {current_page} 页 ===")
            for doc in page_docs:
                print(f"{doc.page_content}\n")
    
    if save_annotated and output_doc:
        output_doc.save(output_path)
        print(f"✅ 已保存标注版PDF到: {output_path}")
        return output_path

# 提取图片并转换为 Markdown
def extract_images_and_convert_to_markdown(elements):
    print("提取图片并转换为 Markdown...")
    # 提取图片并保存
    pdf_doc = fitz_open(pdf_path)
    image_map = {}  # 映射 page_num -> list of image paths

    for page_num, page in enumerate(pdf_doc, start=1):
        image_map[page_num] = []
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            pix = fitz.Pixmap(pdf_doc, xref)
            img_path = os.path.join(output_dir, f"page{page_num}_img{img_index}.png")
            if pix.n < 5:  # RGB / Gray
                pix.save(img_path)
            else:  # CMYK 转 RGB
                pix = fitz.Pixmap(fitz.Colorspace(fitz.CS_RGB), pix)
                pix.save(img_path)
            image_map[page_num].append(img_path)

    # 转换为 Markdown
    md_lines = []
    inserted_images = set()  # 用来记录已经插入过的图片, 避免重复

    for el in elements:
        cat = el.category
        text = el.text
        page_num = el.metadata.page_number

        if cat == "List" and text.strip().startswith("- "):
            md_lines.append(text + "\n")
        elif cat == "Title":
            md_lines.append(f"# {text}\n")
        elif cat in ["Header", "Subheader"]:
            md_lines.append(f"## {text}\n")
        elif cat == "Table":
            if hasattr(el.metadata, "text_as_html") and el.metadata.text_as_html:
                from html2text import HTML2Text
                converter = HTML2Text()
                md_lines.append(converter.handle(el.metadata.text_as_html) + "\n")
            else:
                md_lines.append(el.text + "\n")
        elif cat == "Image":
            # 避免重复插入: 只插入当前图片对应的文件
            for img_path in image_map.get(page_num, []):
                if img_path not in inserted_images:
                    md_lines.append(f"![Image](./{img_path})\n")
                    inserted_images.add(img_path)
        else:
            md_lines.append(text + "\n")

    # 写入 Markdown 文件
    output_md = f"{pdfFileName}.md"
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"✅ 转换完成, 已生成 {output_md} 和 {output_dir}/ 图片文件夹")

# 主函数
def main():
    print("开始处理 PDF...")
    try:
        # 尝试方法1
        docs = load_with_langchain()
        # 可视化所有页面并保存标注版
        render_page(docs, save_annotated=True)
        
        # 尝试方法2
        elements = process_with_unstructured()
        # 转换为 Markdown
        extract_images_and_convert_to_markdown(elements)
        
        print("PDF 处理完成!")
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()