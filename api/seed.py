"""Seed demo data for Nothard (Client / Order / Task / Listing). Idempotent."""

from datetime import datetime

from sqlalchemy import select

from db import SessionLocal, init_db
from models import User, Client, Order, Task, Listing
from catalog import PACKAGE_AMOUNT, PACKAGE_STEPS, SERVICE_PRICE, RUNNER_STEPS
from security import hash_password


def get_or_create_user(email, role, name, password="nothard123"):
    u = SessionLocal.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not u:
        u = User(email=email, password_hash=hash_password(password), name=name, role=role,
                 terms_accepted_at=datetime.utcnow())
        SessionLocal.add(u)
        SessionLocal.flush()
    return u


def add_client(user_id, name, docs, runner_id=None, manager_id=None):
    c = Client(user_id=user_id, name=name, documents=docs, runner_id=runner_id, manager_id=manager_id)
    SessionLocal.add(c)
    SessionLocal.flush()
    return c


def add_package(client, pkg, paid, done_upto, runner_id, field):
    """field: {step_key: (time, addr)} for runner visits; done_upto = index of
    the active step (steps before it are 'done')."""
    order = Order(client_id=client.id, item_type="package", item_id=pkg,
                  amount_gbp=PACKAGE_AMOUNT[pkg], paid=paid,
                  status="active" if paid else "new")
    SessionLocal.add(order)
    SessionLocal.flush()
    for i, key in enumerate(PACKAGE_STEPS[pkg]):
        rid = runner_id if key in RUNNER_STEPS else None
        time, addr = field.get(key, ("", ""))
        status = "done" if i < done_upto else "todo"
        SessionLocal.add(Task(client_id=client.id, order_id=order.id, kind="step", key=key,
                              status=status, runner_id=rid, time=time, addr=addr, position=i))
    return order


def add_service(client, service_id, paid=True):
    order = Order(client_id=client.id, item_type="service", item_id=service_id,
                  amount_gbp=SERVICE_PRICE[service_id], paid=paid,
                  status="active" if paid else "new")
    SessionLocal.add(order)
    SessionLocal.flush()
    SessionLocal.add(Task(client_id=client.id, order_id=order.id, kind="service",
                          key=service_id, status="todo", position=99))
    return order


def run():
    init_db()

    operator = get_or_create_user("operator@nothard.uz", "operator", "Operator")
    aziza = get_or_create_user("aziza@nothard.uz", "operator", "Aziza")  # a manager
    agency = get_or_create_user("agency@nothard.uz", "agency", "London Homes")
    bekzod = get_or_create_user("runner@nothard.uz", "runner", "Bekzod")
    dilshod = get_or_create_user("dilshod@nothard.uz", "runner", "Dilshod")
    client_user = get_or_create_user("client@nothard.uz", "client", "Jasur")
    SessionLocal.commit()

    if not SessionLocal.execute(select(Client)).first():
        # Documents are only those the purchased package/services actually handle.
        docs_premium = {"lease": True, "bank": False, "nhs": False}
        docs_housing = {"lease": False}

        # Jasur — premium, paid, manager assigned, most of the path done, + a service.
        jasur = add_client(client_user.id, "Jasur Karimov", dict(docs_premium),
                           runner_id=bekzod.id, manager_id=aziza.id)
        add_package(jasur, "premium", paid=True, done_upto=6, runner_id=bekzod.id,
                    field={"airportMeet": ("09:30", "Heathrow T2"),
                           "moveIn": ("14:30", "Woolwich, SE18")})
        add_service(jasur, "docTranslate", paid=True)

        # Madina — housing, paid, manager assigned, mid-path.
        madina = add_client(None, "Madina Rustamova", dict(docs_housing),
                            runner_id=bekzod.id, manager_id=aziza.id)
        add_package(madina, "housing", paid=True, done_upto=3, runner_id=bekzod.id,
                    field={"viewings": ("12:00", "Whitechapel, E1"),
                           "moveIn": ("16:00", "Canada Water, SE16")})

        # Timur — housing, UNPAID, no manager, no runner (needs attention).
        timur = add_client(None, "Timur Alimov", dict(docs_housing), runner_id=None, manager_id=None)
        add_package(timur, "housing", paid=False, done_upto=0, runner_id=None, field={})

        # Nilufar — meet (no documents), paid, manager assigned, arrival in progress.
        nilufar = add_client(None, "Nilufar Saidova", {}, runner_id=dilshod.id, manager_id=aziza.id)
        add_package(nilufar, "meet", paid=True, done_upto=1, runner_id=dilshod.id,
                    field={"airportMeet": ("10:00", "Gatwick North")})

        # Otabek — premium, UNPAID, no manager, no runner.
        otabek = add_client(None, "Otabek Yusupov", dict(docs_premium), runner_id=None, manager_id=None)
        add_package(otabek, "premium", paid=False, done_upto=0, runner_id=None, field={})

        SessionLocal.commit()

    if not SessionLocal.execute(select(Listing)).first():
        listings = [
            (1750, "Great Eastern Rd, Stratford E15", "stratford", 1, 1, True, "published", 3),
            (1950, "Surrey Quays Rd, Canada Water SE16", "canadaWater", 2, 1, False, "published", 5),
            (1300, "Mast Quay, Woolwich SE18", "woolwich", 0, 1, True, "moderation", 0),
            (2200, "Olympic Park Ave, Stratford E20", "stratford", 2, 2, True, "published", 2),
            (1600, "Commercial Rd, Whitechapel E1", "whitechapel", 1, 1, True, "moderation", 0),
            (2650, "Deal Porters Way, Canada Water SE16", "canadaWater", 3, 2, False, "published", 1),
        ]
        for price, addr, area, rooms, baths, furn, status, matches in listings:
            SessionLocal.add(Listing(agency_id=agency.id, price_gbp=price, addr=addr, area=area,
                                     rooms=rooms, baths=baths, furnished=furn, status=status, matches=matches))
        SessionLocal.commit()

    print("seed:",
          "clients", len(SessionLocal.execute(select(Client)).scalars().all()),
          "orders", len(SessionLocal.execute(select(Order)).scalars().all()),
          "tasks", len(SessionLocal.execute(select(Task)).scalars().all()),
          "listings", len(SessionLocal.execute(select(Listing)).scalars().all()))
    SessionLocal.remove()


if __name__ == "__main__":
    run()
