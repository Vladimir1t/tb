# ai_search.py
# from fastapi import APIRouter
# from sentence_transformers import SentenceTransformer
# import faiss
# import numpy as np
# import base64
# from database import get_db_connection

# router = APIRouter()

# # Загрузка модели и создание индекса
# model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# def load_embeddings():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT project_id, vector FROM project_embeddings;")
#     rows = cursor.fetchall()
#     conn.close()
#     if not rows:
#         return [], None
#     ids = [r[0] for r in rows]
#     vectors = [np.frombuffer(r[1], dtype="float32") for r in rows]
#     return ids, np.vstack(vectors)

# ids, embeddings = load_embeddings()
# if embeddings is not None:
#     index = faiss.IndexFlatL2(embeddings.shape[1])
#     index.add(embeddings)
# else:
#     index = None

# @router.get("/projects/search/")
# async def search_projects(query: str, top_k: int = 10):
#     if index is None:
#         raise HTTPException(status_code=503, detail="Search index is not available.")

#     q_vec = model.encode([query]).astype("float32")
#     D, I = index.search(q_vec, k=top_k)

#     conn = get_db_connection()
#     cursor = conn.cursor()

#     results = []
#     for idx, dist in zip(I[0], D[0]):
#         pid = ids[idx]
#         cursor.execute("SELECT * FROM projects WHERE id=?", (pid,))
#         row = cursor.fetchone()
#         if row:
#             project = dict(row)
#             if project["icon"]:
#                 project["icon"] = f"data:image/png;base64,{base64.b64encode(project['icon']).decode()}"
#             else:
#                 project["icon"] = None
#             project["similarity"] = float(dist)
#             results.append(project)

#     conn.close()
#     return results