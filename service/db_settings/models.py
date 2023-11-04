from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import mapped_column, DeclarativeBase, Mapped
from datetime import datetime


class Base(DeclarativeBase):
    pass


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id: Mapped[int] = mapped_column(Integer, nullable = False, primary_key = True, autoincrement = True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable = False, default = datetime.now)
    progress: Mapped[int] = mapped_column(Integer, nullable = False, default = 0)

    # ML hyperparams
    prompt: Mapped[str] = mapped_column(Text, nullable = False)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable = True)
    num_steps: Mapped[int] = mapped_column(Integer, nullable = False)

    file_name: Mapped[str | None] = mapped_column(String(255), nullable = True)
