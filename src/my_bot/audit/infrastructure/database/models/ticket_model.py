# my_bot_project/src/my_bot/infrastructure/database/models/ticket_model.py
"""
مدل SQLAlchemy برای جدول تیکت‌های پشتیبانی (TicketModel).

این مدل معادل موجودیت Ticket در لایه دامنه است و نگاشت به جدول tickets را انجام می‌دهد.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from my_bot.infrastructure.database.models import Base
from my_bot.domain.entities.ticket import Ticket, TicketStatus, TicketPriority, TicketCategory
from my_bot.domain.entities.ticket import TicketMessage


class TicketModel(Base):
    """
    مدل SQLAlchemy برای جدول tickets.

    Attributes:
        id: شناسه یکتای تیکت (Primary Key)
        user_id: شناسه کاربر ایجادکننده (Foreign Key to users.id)
        subject: عنوان تیکت
        description: شرح اولیه مشکل
        status: وضعیت تیکت
        priority: اولویت تیکت
        category: دسته‌بندی تیکت
        assigned_to: شناسه کاربر مسئول (اختیاری)
        created_at: زمان ایجاد
        updated_at: زمان آخرین به‌روزرسانی
        resolved_at: زمان حل شدن
        closed_at: زمان بسته شدن
        metadata: داده‌های اضافی (JSON)

    Relationships:
        user: کاربر ایجادکننده
        assignee: کاربر مسئول (ادمین/اپراتور)
        messages: پیام‌های تیکت
    """

    __tablename__ = "tickets"

    # ----------------------------------------------
    # ستون‌های اصلی
    # ----------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # وضعیت و اولویت
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="open", index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")
    category: Mapped[str] = mapped_column(String(30), nullable=False, server_default="general")

    # تخصیص
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # زمان‌ها
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # داده‌های اضافی
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ----------------------------------------------
    # روابط (Relationships)
    # ----------------------------------------------
    # کاربر ایجادکننده
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        foreign_keys=[user_id],
        back_populates="tickets",
        lazy="selectin",
    )

    # کاربر مسئول (ادمین/اپراتور)
    assignee: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        foreign_keys=[assigned_to],
        back_populates="assigned_tickets",
        lazy="selectin",
    )

    # پیام‌های تیکت
    messages: Mapped[List["TicketMessageModel"]] = relationship(
        "TicketMessageModel",
        back_populates="ticket",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TicketMessageModel.created_at",
    )

    # ----------------------------------------------
    # ایندکس‌های اضافی
    # ----------------------------------------------
    __table_args__ = (
        Index("ix_tickets_status_priority", "status", "priority"),
        Index("ix_tickets_assigned_to", "assigned_to"),
        Index("ix_tickets_created_at", "created_at"),
    )

    # ----------------------------------------------
    # متدهای تبدیل به/از دامنه
    # ----------------------------------------------
    def to_domain(self) -> Ticket:
        """
        تبدیل مدل SQLAlchemy به موجودیت دامنه Ticket.

        Returns:
            Ticket: موجودیت دامنه.
        """
        # تبدیل پیام‌ها
        messages = []
        if self.messages:
            for msg_model in self.messages:
                messages.append(msg_model.to_domain())

        return Ticket(
            id=self.id,
            user_id=self.user_id,
            subject=self.subject,
            description=self.description,
            status=TicketStatus(self.status) if self.status else TicketStatus.OPEN,
            priority=TicketPriority(self.priority) if self.priority else TicketPriority.MEDIUM,
            category=TicketCategory(self.category) if self.category else TicketCategory.GENERAL,
            assigned_to=self.assigned_to,
            messages=messages,
            created_at=self.created_at,
            updated_at=self.updated_at,
            resolved_at=self.resolved_at,
            closed_at=self.closed_at,
            metadata=self.metadata or {},
        )

    @classmethod
    def from_domain(cls, ticket: Ticket) -> "TicketModel":
        """
        ساخت مدل SQLAlchemy از موجودیت دامنه Ticket.

        Args:
            ticket: موجودیت دامنه.

        Returns:
            TicketModel: مدل SQLAlchemy.
        """
        from my_bot.infrastructure.database.models.ticket_message_model import TicketMessageModel

        # تبدیل پیام‌ها
        messages = []
        for msg in ticket.messages:
            messages.append(TicketMessageModel.from_domain(msg))

        return cls(
            id=ticket.id,
            user_id=ticket.user_id,
            subject=ticket.subject,
            description=ticket.description,
            status=ticket.status.value if ticket.status else TicketStatus.OPEN.value,
            priority=ticket.priority.value if ticket.priority else TicketPriority.MEDIUM.value,
            category=ticket.category.value if ticket.category else TicketCategory.GENERAL.value,
            assigned_to=ticket.assigned_to,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            resolved_at=ticket.resolved_at,
            closed_at=ticket.closed_at,
            metadata=ticket.metadata,
            messages=messages,
        )

    def __repr__(self) -> str:
        """نمایش رشته‌ای مدل."""
        return f"<TicketModel(id={self.id}, subject={self.subject}, status={self.status}, user_id={self.user_id})>"