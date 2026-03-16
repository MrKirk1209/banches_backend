from fastapi import FastAPI, Request
import os
from typing import Union
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine

from starlette.middleware.sessions import SessionMiddleware
from app.admin_auth import authentication_backend # <--- Импортируем нашу логику
from app.config import settings

from app.routers.complaint import apply_complaint_action
from sqladmin import Admin, ModelView,action

from app.map.models import (
    Complaint, ComplaintReason, ComplaintStatus, User, Role, LocationSeat, Review, Picture,
    TypeOfSeat, Status, Pollution, Condition, Material,
    LocationSeatOfReview
)
from app.routers import (
    auth_router,
    locations_router,
    reviews_router,
    dict_router,
    pictures_router,
    users_router,
    complaint_router,
)


app = FastAPI()

# Включите CORS для Android
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY) 
app.include_router(auth_router,)

app.include_router(locations_router,)
app.include_router(reviews_router,)
app.include_router(dict_router,)
app.include_router(pictures_router,)
app.include_router(users_router,)
app.include_router(complaint_router,)

admin = Admin(
    app, 
    engine, 
    authentication_backend=authentication_backend 
)
class ComplaintAdmin(ModelView, model=Complaint):
    name = "Жалоба"
    name_plural = "Жалобы"
    icon = "fa-solid fa-flag"

    column_list = [
        "id",
        "status_ref",      
        "reason_ref",     
        "author",          
        "location",         
        "picture",         
        "reported_user",  
        "text",
        "resolved_by",    
    ]

    column_searchable_list = [Complaint.id, Complaint.text]
    

    # если не хочешь, чтобы в админке вручную создавали жалобы:
    can_create = False

    @action(
        name="approve_complaints",
        label="Одобрить",
        confirmation_message="Одобрить выбранные жалобы?",
        add_in_detail=True,
        add_in_list=True,
    )
    async def approve_complaints(self, request: Request):
        """
        Меняет статус жалоб на 'Одобрена' (2) и запускает логику из API.
        """
        # стандартный способ из доки sqladmin
        pks = request.query_params.get("pks", "").split(",")  # ["1","2","3",...]
        for pk in filter(None, pks):
            # удобный helper от sqladmin: вернёт объект по PK и session уже подхватит engine
            complaint: Complaint = await self.get_object_for_edit(pk)
            if not complaint:
                continue
            complaint.status_id = 2
            complaint.resolved_by_id = None  # или сюда можно пробросить id модератора, если нужно
            # apply_complaint_action сам использует тот же session, что и self.session
            await apply_complaint_action(complaint, self.session)

        await self.session.commit()

        referer = request.headers.get("Referer")
        if referer:
            return RedirectResponse(referer)
        return RedirectResponse(request.url_for("admin:list", identity=self.identity))

    @action(
        name="reject_complaints",
        label="Отклонить",
        confirmation_message="Отклонить выбранные жалобы?",
        add_in_detail=True,
        add_in_list=True,
    )
    async def reject_complaints(self, request: Request):
        """
        Меняет статус жалоб на 'Отклонена' (3) без доп. действий.
        """
        pks = request.query_params.get("pks", "").split(",")
        for pk in filter(None, pks):
            complaint: Complaint = await self.get_object_for_edit(pk)
            if not complaint:
                continue
            complaint.status_id = 3
            complaint.resolved_by_id = None  # или current_admin.id, если будешь пробрасывать

        await self.session.commit()

        referer = request.headers.get("Referer")
        if referer:
            return RedirectResponse(referer)
        return RedirectResponse(request.url_for("admin:list", identity=self.identity))
    
class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    column_list = [User.id, User.Username, User.email, User.role]
    column_searchable_list = [User.Username, User.email]
    column_sortable_list = [User.id]

# 2. Роли
class RoleAdmin(ModelView, model=Role):
    name = "Роль"
    name_plural = "Роли"
    icon = "fa-solid fa-user-tag"
    column_list = [Role.id, Role.role_name]

# 3. Локации (Лавочки)
class LocationSeatAdmin(ModelView, model=LocationSeat):
    name = "Локация"
    name_plural = "Локации"
    icon = "fa-solid fa-map-location-dot"
    column_list = [
        LocationSeat.id, 
        LocationSeat.name, 
        LocationSeat.status_ref, 
        LocationSeat.type_ref, 
        LocationSeat.author
    ]
    column_searchable_list = [LocationSeat.name, LocationSeat.address]
    column_sortable_list = [LocationSeat.id, LocationSeat.created_at] 

# 4. Отзывы
class ReviewAdmin(ModelView, model=Review):
    name = "Отзыв"
    name_plural = "Отзывы"
    icon = "fa-solid fa-star"
    column_list = [
        Review.id, 
        Review.rate, 
        Review.author, 
        Review.pollution_ref,
        Review.condition_ref,
        Review.material_ref
    ]
    column_sortable_list = [Review.created_at, Review.rate]

# 5. Картинки
class PictureAdmin(ModelView, model=Picture):
    name = "Фотография"
    name_plural = "Фотографии"
    icon = "fa-solid fa-image"
    column_list = [Picture.id, Picture.url, Picture.location, Picture.uploader]

# --- СПРАВОЧНИКИ (Dictionaries) ---

class TypeOfSeatAdmin(ModelView, model=TypeOfSeat):
    name = "Тип места"
    name_plural = "Типы мест"
    icon = "fa-solid fa-chair"
    column_list = [TypeOfSeat.id, TypeOfSeat.name]

class StatusAdmin(ModelView, model=Status):
    name = "Статус"
    name_plural = "Статусы"
    icon = "fa-solid fa-info-circle"
    column_list = [Status.id, Status.name]

class PollutionAdmin(ModelView, model=Pollution):
    name = "Загрязнение"
    name_plural = "Загрязнения"
    icon = "fa-solid fa-trash"
    column_list = [Pollution.id, Pollution.name]

class ConditionAdmin(ModelView, model=Condition):
    name = "Состояние"
    name_plural = "Состояния"
    icon = "fa-solid fa-hammer"
    column_list = [Condition.id, Condition.name]

class MaterialAdmin(ModelView, model=Material):
    name = "Материал"
    name_plural = "Материалы"
    icon = "fa-solid fa-layer-group"
    column_list = [Material.id, Material.name]



class LocationSeatOfReviewAdmin(ModelView, model=LocationSeatOfReview):
    name = "Связь Локация-Отзыв"
    name_plural = "Связи Локация-Отзыв"
    icon = "fa-solid fa-link"
    column_list = [LocationSeatOfReview.id, LocationSeatOfReview.location, LocationSeatOfReview.review]

class Complaint_StatusAdmin(ModelView, model=ComplaintStatus):
    name = "Статус жалобы"
    name_plural = "Статусы жалоб"
    icon = "fa-solid fa-layer-group"
    column_list = [ComplaintStatus.id, ComplaintStatus.name]

class Complaint_ReasonAdmin(ModelView, model=ComplaintReason):
    name = "Причина жалобы"
    name_plural = "Причины жалоб"
    icon = "fa-solid fa-layer-group"
    column_list = [ComplaintReason.id, ComplaintReason.name]

admin.add_view(UserAdmin)
admin.add_view(RoleAdmin)
admin.add_view(LocationSeatAdmin)
admin.add_view(ReviewAdmin)
admin.add_view(PictureAdmin)


admin.add_view(TypeOfSeatAdmin)
admin.add_view(StatusAdmin)
admin.add_view(PollutionAdmin)
admin.add_view(ConditionAdmin)
admin.add_view(MaterialAdmin)


admin.add_view(LocationSeatOfReviewAdmin)
admin.add_view(Complaint_StatusAdmin)
admin.add_view(Complaint_ReasonAdmin)
admin.add_view(ComplaintAdmin)