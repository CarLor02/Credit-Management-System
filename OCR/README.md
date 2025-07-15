# 文档处理工具

一个功能强大的文档处理工具，支持将PDF、Excel、HTML和图像文件转换为Markdown格式。

## 功能特点

- **多格式支持**：处理PDF、Excel、HTML和图像文件
- **批量处理**：支持批量处理整个文件夹中的文档
- **递归处理**：可选择递归处理子文件夹
- **保持目录结构**：可选择在输出中保持原始目录结构
- **智能处理**：
  - PDF处理：支持普通PDF和扫描PDF（使用云雾AI的Gemini模型进行OCR）
  - Excel处理：支持合并单元格、多工作表、公式计算结果
  - HTML处理：清理HTML并转换为Markdown
  - 图像处理：使用云雾AI的Gemini模型提取图像中的文本

## 安装依赖

```bash
pip install -r requirements.txt
```

### 依赖包

- **通用依赖**：
  - pandas
  - pathlib
  - argparse
  - logging

- **PDF处理依赖**：
  - docling
  - docling_core

- **Excel处理依赖**：
  - pandas
  - openpyxl
  - xlrd

- **HTML处理依赖**：
  - beautifulsoup4
  - html2text
  - requests

- **图像处理依赖**：
  - openai (用于调用云雾AI API)
  - pillow

## 使用方法

### 命令行使用

```bash
python process_docs.py --input <输入文件夹> --output <输出文件夹> --type <文件类型> [选项]
```

#### 参数说明

- `--input`, `-i`: 输入文件夹路径（默认: ./pdf_files）
- `--output`, `-o`: 输出文件夹路径（默认: ./output）
- `--type`, `-t`: 要处理的文件类型，可选值: pdf, excel, html, image, all（默认: all）
- `--save-intermediate`, `-s`: 是否保存中间文件（默认: True）
- `--api-key`, `-k`: 云雾AI API密钥（也可通过环境变量设置）
- `--recursive`, `-r`: 是否递归处理子文件夹（默认: True）
- `--model`, `-m`: 使用的Gemini模型名称（默认: gemini-2.0-flash-thinking-exp-01-21）
- `--preserve-structure`, `-p`: 是否保持原始目录结构（默认: True）

### 示例

```bash
# 处理所有类型文件
python process_docs.py --input ./documents --output ./output

# 只处理PDF文件
python process_docs.py --type pdf --input ./pdf_files --output ./output

# 只处理Excel文件
python process_docs.py --type excel --input ./excel_files --output ./output

# 只处理HTML文件
python process_docs.py --type html --input ./html_files --output ./output

# 只处理图像文件
python process_docs.py --type image --input ./image_files --output ./output
```

### 环境变量设置

对于需要使用云雾AI API的功能（扫描PDF和图像处理），需要设置API密钥：

```bash
export YUNWU_API_KEY='your-api-key'
```

## 注意事项

1. **PDF处理**：
   - 处理扫描PDF需要云雾AI API密钥
   - 普通PDF处理依赖docling库，确保已正确安装

2. **Excel处理**：
   - 支持.xlsx和.xls格式
   - 处理包含合并单元格的Excel文件
   - 显示公式计算结果而非公式本身

3. **HTML处理**：
   - 自动清理HTML注释和不必要的标签
   - 保留表格结构

4. **图像处理**：
   - 需要云雾AI API密钥
   - 支持常见图像格式：jpg, jpeg, png, gif, webp, bmp, tiff, tif

5. **内存使用**：
   - 处理大型文件可能需要较多内存
   - 处理大量文件时建议分批进行

## 单独处理特定类型文件

除了使用主程序 `process_docs.py` 外，还可以使用专门的脚本处理特定类型的文件：

- `process_pdf.py`: 处理PDF文件
- `process_excel.py`: 处理Excel文件
- `process_html.py`: 处理HTML文件
- `process_images.py`: 处理图像文件

## 故障排除

- **缺少依赖**：如果遇到ImportError，请确保已安装所有必要的依赖包
- **API密钥问题**：确保正确设置了云雾AI API密钥
- **内存不足**：处理大文件时可能遇到内存不足问题，尝试增加系统内存或减少批处理文件数量
- **编码问题**：如果遇到编码错误，程序会尝试自动修复，但某些特殊情况可能需要手动处理

## 贡献

欢迎提交问题报告和改进建议！

## 许可证

[MIT License](LICENSE)