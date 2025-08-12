from typing import Optional, Dict, List
from uuid import uuid4, UUID
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl, field_validator

app = FastAPI()

# ----- Pydantic schema (input/output) -----
class MovieCreate(BaseModel):
    title: str
    year: int
    director: Optional[str] = None
    synopsis: Optional[str] = None
    poster_url: Optional[HttpUrl] = None
    source: Optional[str] = None        # e.g., "tmdb", "imdb"
    source_id: Optional[str] = None     # e.g., "tt1375666"

    @field_validator("year")
    @classmethod
    def check_year(cls, v: int) -> int:
        current_year = date.today().year
        if v < 1888 or v > current_year + 1:
            raise ValueError(f"year must be between 1888 and {current_year + 1}")
        return v

class Movie(MovieCreate):
    id: UUID

# ----- In-memory "database" of Python objects -----
# Key = UUID, Value = Movie (a Pydantic model, which is also a Python object)
MOVIES: Dict[UUID, Movie] = {}

# ----- Routes -----

@app.post("/movies", response_model=Movie, status_code=201)
def create_movie(movie_in: MovieCreate):
    """
    Accepts JSON like:
    {
      "title": "Inception",
      "year": 2010,
      "director": "Christopher Nolan",
      "poster_url": "https://image/",
      "source": "imdb",
      "source_id": "tt1375666"
    }
    """
    movie_id = uuid4()
    movie_obj = Movie(id=movie_id, **movie_in.model_dict())
    MOVIES[movie_id] = movie_obj
    return movie_obj

@app.get("/movies", response_model=List[Movie])
def list_movies():
    """Return all stored movies (unsorted)."""
    return list(MOVIES.values())

@app.get("/movies/{movie_id}", response_model=Movie)
def get_movie(movie_id: UUID):
    movie = MOVIES.get(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@app.put("/movies/{movie_id}", response_model=Movie)
def update_movie(movie_id: UUID, movie_in: MovieCreate):
    """
    Replace all fields for a movie (simple full update).
    """
    if movie_id not in MOVIES:
        raise HTTPException(status_code=404, detail="Movie not found")
    updated = Movie(id=movie_id, **movie_in.model_dict())
    MOVIES[movie_id] = updated
    return updated

@app.delete("/movies/{movie_id}", status_code=204)
def delete_movie(movie_id: UUID):
    if movie_id not in MOVIES:
        raise HTTPException(status_code=404, detail="Movie not found")
    del MOVIES[movie_id]
    return None


from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import html

# ---------- Simple HTML homepage with a form ----------
@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    # Build a simple list of movies already stored
    items_html = []
    for m in MOVIES.values():
        items_html.append(
            f"""
            <li style="margin:8px 0; list-style: none; display:flex; gap:10px; align-items:center;">
                {'<img src="'+html.escape(m.poster_url)+'" alt="poster" style="height:60px;">' if m.poster_url else ''}
                <div>
                  <strong>{html.escape(m.title)}</strong> ({m.year})<br>
                  <small>{html.escape(m.director or '')}</small>
                </div>
            </li>
            """
        )
    movies_list = "\n".join(items_html) if items_html else "<li>No movies yet. Be the first!</li>"

    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Submit a Movie</title>
        <style>
          body {{ font-family: -apple-system, system-ui, Segoe UI, Roboto, sans-serif; margin: 24px; }}
          .card {{ max-width: 640px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; }}
          label {{ display:block; font-size: 14px; margin-top: 10px; }}
          input, textarea {{ width: 100%; padding: 10px; border: 1px solid #e5e7eb; border-radius: 8px; }}
          button {{ margin-top: 14px; padding: 10px 14px; border-radius: 10px; border: 1px solid #111827; background:#111827; color:white; cursor:pointer; }}
          ul {{ padding-left: 0; }}
          h1,h2 {{ margin: 10px 0; }}
        </style>
      </head>
      <body>
        <h1>What movie are you into right now?</h1>
        <div class="card">
          <form method="POST" action="/submit_movie">
            <label>Title
              <input required name="title" placeholder="Inception" />
            </label>
            <label>Year
              <input required name="year" type="number" min="1888" max="2100" placeholder="2010" />
            </label>
            <label>Director
              <input name="director" placeholder="Christopher Nolan" />
            </label>
            <label>Poster URL
              <input name="poster_url" placeholder="https://..." />
            </label>
            <label>Synopsis
              <textarea name="synopsis" rows="3" placeholder="Optional note"></textarea>
            </label>
            <label>Source (tmdb / imdb)
              <input name="source" placeholder="imdb" />
            </label>
            <label>Source ID
              <input name="source_id" placeholder="tt1375666" />
            </label>
            <button type="submit">Add Movie</button>
          </form>
        </div>

        <h2 style="margin-top:24px;">Recently submitted</h2>
        <ul>
          {movies_list}
        </ul>

        <p style="margin-top:20px;">
          Prefer JSON? Try the API: <code>POST /movies</code> (see <a href="/docs">/docs</a>)
        </p>
      </body>
    </html>
    """

# ---------- Form handler that converts form fields -> Python object ----------
@app.post("/submit_movie")
def submit_movie(
    title: str = Form(...),
    year: int = Form(...),
    director: Optional[str] = Form(None),
    synopsis: Optional[str] = Form(None),
    poster_url: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    source_id: Optional[str] = Form(None),
):
    # Build a MovieCreate (Pydantic will validate types)
    mc = MovieCreate(
        title=title,
        year=year,
        director=director,
        synopsis=synopsis,
        poster_url=poster_url,
        source=source,
        source_id=source_id,
    )
    # Reuse the same logic as the JSON endpoint
    created = create_movie(mc)

    # Redirect back to homepage after submit
    return RedirectResponse(url="/", status_code=303)
