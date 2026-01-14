import os
import json
from google.cloud import vision_v1 as vision

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../../local/google-vision/vision-project.json"

def structured_text_with_boxes(image_path):
    client = vision.ImageAnnotatorClient()

    with open(image_path, "rb") as img_file:
        content = img_file.read()
    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    if response.error.message:
        raise Exception(f"API Error: {response.error.message}")

    results = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            # Reconstruct block text
            block_text = ""
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        block_text += symbol.text
                    block_text += " "
                block_text = block_text.strip() + "\n"
            block_text = block_text.strip()

            # Extract bounding box vertices
            vertices = [
                {"x": v.x, "y": v.y}
                for v in block.bounding_box.vertices
            ]

            results.append({
                "block_text": block_text,
                "confidence": block.confidence,
                "bounding_box": vertices
            })

    return results

if __name__ == "__main__":
    import os
    # for all images in the image directory
    # we call the function structured_text_with_boxes
    # then we save the results to a json file in a different directory but with a related name
    print(f"Current working directory: {os.getcwd()} ")
    # if you want to process all images in a directory, you can use os.listdir
    # and loop through the files
    for filename in os.listdir("D:/ALF/images/"):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            image_path = os.path.join("D:/ALF/images/", filename)
            structured = structured_text_with_boxes(image_path)

            # Save structured JSON with bounding boxes
            output_filename = f"{os.path.splitext(filename)[0]}.json"
            output_path = os.path.join("D:/ALF/structured_outputs/", output_filename)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(structured, f, ensure_ascii=False, indent=4)

            print(f"Saved structured JSON with bounding boxes to {output_path}")
    
