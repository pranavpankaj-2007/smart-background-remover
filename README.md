# Smart Background Remover

An AI-powered background removal and image editing web application built with **Python, Streamlit, and rembg**.

Smart Background Remover allows users to remove image backgrounds, create transparent PNGs, replace backgrounds, and fine-tune the final image with simple editing controls.

## Features

- **AI-Powered Background Removal** — Remove image backgrounds using the pretrained `rembg` model.
- **Transparent PNG Export** — Download images with transparent backgrounds.
- **Solid Colour Backgrounds** — Replace the original background with a colour of your choice.
- **Custom Image Backgrounds** — Place the subject over another image.
- **Edge Refinement** — Adjust edge blending and softness for a more natural appearance.
- **Shadow Controls** — Customize shadow strength, softness, and vertical offset.
- **Image Adjustments** — Fine-tune subject brightness and warmth.
- **Live Preview** — Preview editing changes before exporting.
- **Full-Resolution Export** — Prepare a high-resolution result for download.

## Tech Stack

- **Python** — Application logic and image processing
- **Streamlit** — Interactive web interface
- **rembg** — Pretrained background removal model
- **ONNX Runtime** — Model inference
- **Pillow (PIL)** — Image manipulation
- **NumPy** — Image array processing

## Project Structure

```text
smart-background-remover/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/pranavpankaj-2007/smart-background-remover.git
```

### 2. Navigate to the project directory

```bash
cd smart-background-remover
```

### 3. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt instead or consult the Python virtual environment documentation.

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run the application

```bash
streamlit run app.py
```

Streamlit will provide a local URL, usually:

```text
http://localhost:8501
```

Open that address in your browser to use the application.

## How to Use

1. Launch the application.
2. Upload an image.
3. Let the background removal process finish.
4. Choose a transparent, solid-colour, or custom image background.
5. Adjust edge refinement, shadow, brightness, and warmth settings as desired.
6. Preview the result.
7. Download the transparent PNG or prepare and download the full-resolution result.

## Notes

- The application uses a pretrained `rembg` model; it does not train a model from scratch.
- The first background removal may take longer because the required model may need to be downloaded.
- Processing time and memory usage depend on image dimensions and available system resources.
- Complex edges, hair, and similar foreground details may require additional adjustment.
- A compatible Python environment and the dependencies listed in `requirements.txt` are required.

## Future Improvements

- Add sample before-and-after images.
- Improve edge refinement for complex subjects.
- Add more background effects and editing options.
- Deploy a public web demo.

## Author

**Pranav Pankaj**

GitHub: [@pranavpankaj-2007](https://github.com/pranavpankaj-2007)

## License

No license has been specified yet. Unless a license is added, the repository's code is not automatically granted an open-source license for reuse or redistribution.
