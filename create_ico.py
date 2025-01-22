from PIL import Image, ImageEnhance
import os

def create_ico():
    """
    将 avatar_user.png 转换为 icon.ico
    生成超大尺寸高质量图标
    """
    # 使用 avatar_user.png 作为源文件
    source_file = os.path.join('pet_image', 'avatar_user.png')
    
    if not os.path.exists(source_file):
        print(f"未找到源文件: {source_file}")
        return
    
    # 打开源文件
    with Image.open(source_file) as img:
        # 确保图像为RGBA模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 首先将图像调整为超大尺寸以保持质量
        base_size = (1024, 1024)
        img = img.resize(base_size, Image.Resampling.LANCZOS)
        
        # 增强原始图像的清晰度
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)  # 增强锐度
        
        # 增强对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)  # 适度增强对比度
        
        # 创建多个尺寸的图标，主要使用较大尺寸
        sizes = [(512, 512), (256, 256), (128, 128), (64, 64), (48, 48)]
        images = []
        
        for size in sizes:
            # 从基础大图中缩放，保持最佳质量
            resized_img = img.resize(size, Image.Resampling.LANCZOS)
            images.append(resized_img)
        
        # 保存为 ICO 文件，使用最大尺寸作为主图标
        icon_path = os.path.join('pet_image', 'icon.ico')
        images[0].save(
            icon_path, 
            format='ICO',
            sizes=sizes,
            append_images=images[1:],
            optimize=False  # 关闭优化以保持质量
        )
        print(f"图标已保存到: {icon_path}")

if __name__ == '__main__':
    create_ico() 