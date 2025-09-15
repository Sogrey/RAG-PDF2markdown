import os
import re
import shutil

def rename_images_with_prefix(md_file_path, image_dir_path, prefix):
    """
    重命名Markdown文件中引用的图像资源，添加指定前缀，并更新引用路径。
    未被引用的图像将被删除。
    
    Args:
        md_file_path: Markdown文件路径
        image_dir_path: 图像资源目录路径
        prefix: 要添加的前缀
    """
    # 读取Markdown文件内容
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 使用正则表达式查找所有图像引用
    # 匹配格式如 ![Image](./1\page8_img1.png) 或 ![Image](./1/page8_img1.png)
    image_pattern = r'!\[.*?\]\((\.\/1[\/\\]([^)]+))\)'
    image_matches = re.findall(image_pattern, md_content)
    
    # 获取所有引用的图像文件名
    referenced_images = [match[1] for match in image_matches]
    print(f"在Markdown文件中找到 {len(referenced_images)} 个图像引用")
    
    # 获取图像目录中的所有图像文件
    all_images = [f for f in os.listdir(image_dir_path) if os.path.isfile(os.path.join(image_dir_path, f))]
    print(f"图像目录中有 {len(all_images)} 个图像文件")
    
    # 重命名引用的图像并更新Markdown文件
    renamed_images = {}  # 存储原文件名到新文件名的映射
    
    for old_name in referenced_images:
        if old_name in all_images:
            # 创建新文件名（添加前缀）
            new_name = f"{prefix}_{old_name}"
            old_path = os.path.join(image_dir_path, old_name)
            new_path = os.path.join(image_dir_path, new_name)
            
            # 重命名文件
            shutil.copy2(old_path, new_path)  # 先复制，确保操作安全
            renamed_images[old_name] = new_name
            print(f"重命名: {old_name} -> {new_name}")
    
    # 更新Markdown文件中的引用路径
    for match in image_matches:
        old_ref = match[0]  # 完整的引用路径
        old_name = match[1]  # 仅文件名部分
        
        if old_name in renamed_images:
            new_name = renamed_images[old_name]
            # 替换引用路径中的文件名部分
            new_ref = old_ref.replace(old_name, new_name)
            md_content = md_content.replace(old_ref, new_ref)
    
    # 保存更新后的Markdown文件
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"已更新Markdown文件中的图像引用路径")
    
    # 删除未被引用的图像
    for img in all_images:
        if img not in referenced_images:
            os.remove(os.path.join(image_dir_path, img))
            print(f"删除未引用的图像: {img}")
    
    # 删除原始的已重命名图像
    for old_name in renamed_images.keys():
        os.remove(os.path.join(image_dir_path, old_name))
        print(f"删除原始图像: {old_name}")
    
    print("操作完成！")

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python rename_images.py 文件名 [前缀]")
        print("示例: python rename_images.py 1 dify")
        print("      python rename_images.py 1")
        sys.exit(1)
    
    # 获取文件名（必须参数）
    file_name = sys.argv[1]
    
    # 获取前缀（可选参数），如果未提供则使用文件名加下划线
    if len(sys.argv) < 3:
        prefix = f"{file_name}_"
    else:
        prefix = sys.argv[2]
    
    md_file_path = f"{file_name}.md"
    image_dir_path = file_name
    
    print(f"处理文件: {md_file_path}")
    print(f"图像目录: {image_dir_path}")
    print(f"添加前缀: {prefix}")
    
    rename_images_with_prefix(md_file_path, image_dir_path, prefix)