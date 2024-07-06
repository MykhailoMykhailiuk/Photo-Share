import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

default_avatar_url = "https://res.cloudinary.com/dl3r3kuc7/image/upload/v1719001257/default_avatar_siyhvc.png"


class Base(DeclarativeBase):
    pass


image_tag_table = Table(
    "image_tags",
    Base.metadata,
    Column("image_id", Integer, ForeignKey("images.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)
    images: Mapped[list["Image"]] = relationship(
        "Image", secondary=image_tag_table, back_populates="tags"
    )


class Image(Base):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="images", lazy="joined")
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="image", cascade="all, delete-orphan"
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary=image_tag_table, back_populates="images"
    )


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    image: Mapped["Image"] = relationship("Image", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Enum] = mapped_column(
        "role", Enum(Role), default=Role.user, nullable=True
    )
    access_token: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    avatar: Mapped[str] = mapped_column(
        String(255), nullable=True, default=default_avatar_url
    )
    images: Mapped[list["Image"]] = relationship("Image", back_populates="user")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")
