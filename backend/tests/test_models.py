from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database import build_engine
from app.models import Base, ChatMessage, ChatSession, Document, Review, ReviewItem


def test_create_all_builds_five_business_tables(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'models.db'}")
    Base.metadata.create_all(engine)

    assert set(inspect(engine).get_table_names()) == {
        "documents",
        "reviews",
        "review_items",
        "chat_sessions",
        "chat_messages",
    }


def test_document_delete_cascades_related_rows(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'cascade.db'}")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        document = Document(
            filename="contract.txt",
            stored_filename="safe.txt",
            storage_path=str(tmp_path / "safe.txt"),
            file_type="txt",
            file_size=12,
        )
        review = Review(document=document, summary="summary", status="completed")
        review.items.append(
            ReviewItem(
                category="合规风险",
                severity="high",
                title="风险",
                description="描述",
                suggestion="建议",
                source_text="原文",
            )
        )
        session = ChatSession(document=document)
        session.messages.append(ChatMessage(role="user", content="问题"))
        db.add(document)
        db.commit()
        db.delete(document)
        db.commit()

        assert db.query(Review).count() == 0
        assert db.query(ReviewItem).count() == 0
        assert db.query(ChatSession).count() == 0
        assert db.query(ChatMessage).count() == 0

