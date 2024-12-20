from fastapi import FastAPI, HTTPException
from youtube_community_tab.post import Post
from youtube_community_tab.community_tab import CommunityTab

app = FastAPI()


# --- RUTA PRINCIPAL ---
@app.get("/", tags=["General"])
def read_root():
    return {"message": "Bienvenido a la API de la pestaña de comunidad de YouTube"}

# --- RUTAS DE POSTS ---
@app.get("/find-all-posts/{channel_name}", tags=["Posts"])
def get_posts(channel_name: str):
    try:
        community_tab = CommunityTab(f'@${channel_name}')
        community_tab.load_posts()
        if not community_tab.posts:
            raise HTTPException(status_code=404, detail="No se encontraron publicaciones para este canal")
        return [post.as_json() for post in community_tab.posts]

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener datos del canal: {channel_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/post/{post_id}", tags=["Posts"])
def get_post(post_id: str):
    try:
        post = Post.from_post_id(post_id)
        return post.as_json()

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener el post: {post_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posts/{post_id}/stats", tags=["Posts"])
def get_post_stats(post_id: str):
    try:
        post = Post.from_post_id(post_id)
        post_data = post.as_json()

        likes = post_data.get("vote_count", {}).get("simpleText", "0")
        likes = int(likes.replace(" Me gusta", "").replace(",", ""))  # Limpiar texto y convertir a entero

        # Llamar directamente a la función `get_comments`
        comments = get_comments(post_id)
        comments_count = len(comments) if isinstance(comments, list) else 0

        return {
            "post_id": post_id,
            "likes": likes,
            "comments": comments_count
        }

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener estadísticas del post: {post_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/posts/{post_id}/comments", tags=["Comments"])
def create_comment(post_id: str, comment: str):
    try:
        post = Post.from_post_id(post_id)
        post.create_comment(comment)
        return {"message": "Comentario creado exitosamente"}

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo crear el comentario en el post: {post_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posts/{post_id}/comments", tags=["Comments"])
def get_comments(post_id: str):
    try:
        post = Post.from_post_id(post_id)
        post.load_comments()
        comments = [comment.as_json() for comment in getattr(post, "comments", [])]

        if not comments:
            raise HTTPException(status_code=404, detail=f"No se encontraron comentarios para el post: {post_id}")

        return comments

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudieron obtener comentarios del post: {post_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- RUTAS DE COMUNIDAD ---
@app.get("/community/{channel_name}/info", tags=["Community"])
def get_community_info(channel_name: str):
    try:
        community_tab = CommunityTab(channel_name)
        community_tab.load_posts()

        return {
            "channel_id": community_tab.channel_id,
            "posts_count": len(community_tab.posts),
            "visitor_data": community_tab.visitor_data,
        }

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener la información del canal: {channel_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/community/{channel_name}/posts", tags=["Community"])
def get_paginated_posts(channel_name: str, page: int = 1, per_page: int = 10):
    try:
        community_tab = CommunityTab(channel_name)
        community_tab.load_posts()

        start = (page - 1) * per_page
        end = start + per_page

        return [post.as_json() for post in community_tab.posts[start:end]]

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudieron obtener publicaciones del canal: {channel_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

