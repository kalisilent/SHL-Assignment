import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def build_vector_index():
    print("Loading catalog...")
    with open('data/catalog.json', 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    # We use a fast, free, local embedding model
    print("Loading embedding model (this might download a ~80MB model on first run)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Encoding 389 assessments into vectors...")
    # We create a rich text string for the AI to understand what each item is
    texts_to_embed = []
    for item in catalog:
        url = item.get("url", "")
        url_slug = url.replace("https://www.shl.com/products/product-catalog/view/", "")
        url_slug = url_slug.replace("/", " ")
        text = (
            f"Assessment Name: {item['name']}. "
            f"Test Type: {item['test_type']}. "
            f"URL: {url_slug}."
        )
        texts_to_embed.append(text)

    # Convert text to vector embeddings
    embeddings = model.encode(texts_to_embed)
    embeddings = np.array(embeddings).astype('float32')

    # Build the FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # Save the index to disk
    faiss.write_index(index, 'data/catalog.index')
    print("Successfully built and saved FAISS index to data/catalog.index!")

if __name__ == "__main__":
    build_vector_index()