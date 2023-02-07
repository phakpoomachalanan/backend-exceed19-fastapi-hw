from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
from os import getenv

DATABASE_NAME = "exceed09"
COLLECTION_NAME = "reservation"
MONGO_DB_DOM = "mongo.exceed19.online"
MONGO_DB_PORT = 8443

class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int

load_dotenv(".env")
username = getenv("username")
password = getenv("password")

client = MongoClient(f"mongodb://{username}:{password}@{MONGO_DB_DOM}:{MONGO_DB_PORT}/?authMechanism=DEFAULT")

db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
app = FastAPI()

def room_avaliable(room_id: int, start_date: str, end_date: str):
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0

@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name:str):
    result = list(collection.find({"name": name}))
    if len(result) == 0:
        return {
            "result": result
        }
    result = result[0]
    return {
        "result": [{
            "name": name,
            "start_date": result["start_date"],
            "end_date": result["end_date"],
            "room_id": result["room_id"]
        }]
    }

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    result = list(collection.find({"room_id": room_id}))
    if len(result) == 0:
        return {
            "result": result
        }
    result = result[0]
    return {
        "result": [{
            "name": result["name"],
            "start_date": result["start_date"],
            "end_date": result["end_date"],
            "room_id": room_id
        }]
    }

@app.post("/reservation")
def reserve(reservation : Reservation):
    start_date = reservation.start_date.strftime("%Y-%m-%d")
    end_date = reservation.end_date.strftime("%Y-%m-%d")
    room_id = reservation.room_id
    if (start_date > end_date):
        raise HTTPException(status_code=400, detail="Reservation can not be made")
    if (room_id<1 or room_id>10):
        raise HTTPException(status_code=400, detail="Reservation can not be made")
    if not room_avaliable(room_id, start_date, end_date):
        raise HTTPException(status_code=400, detail="Reservation can not be made")
    collection.insert_one({
        "name": reservation.name,
        "start_date": start_date,
        "end_date": end_date,
        "room_id": room_id
    })

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    start_date = reservation.start_date.strftime("%Y-%m-%d")
    end_date = reservation.end_date.strftime("%Y-%m-%d")
    room_id = reservation.room_id
    new_start_date = new_start_date.strftime("%Y-%m-%d")
    new_end_date = new_end_date.strftime("%Y-%m-%d")
    if (new_start_date > new_end_date):
        raise HTTPException(status_code=400, detail="Reservation can not be made")
    if room_avaliable(room_id, new_start_date, new_end_date):
        collection.update_one({
            "room_id": room_id, 
            "start_date": start_date, 
            "end_date": end_date
            }, 
            {
                "$set": {
                    "start_date": new_start_date,
                    "end_date": new_end_date
                }
            }
        )
    else:
        raise HTTPException(status_code=400, detail="Reservation can not be made")

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    start_date = reservation.start_date.strftime("%Y-%m-%d")
    end_date = reservation.end_date.strftime("%Y-%m-%d")
    room_id = reservation.room_id
    if (start_date > end_date):
        raise HTTPException(status_code=400, detail="Reservation not found")
    if (room_id<1 or room_id>10):
        raise HTTPException(status_code=400, detail="Reservation not found")
    collection.delete_one({"room_id": room_id, "start_date": start_date, "end_date": end_date})

"""
#update ข้อมูลใน collection 
filter = {'name': 'person1'}
update = {'$set': {'name': 'person2'}}
colletion.update_one(filter, update)
colletion.update_many(filter, update)

#delete ลบข้อมูลใน collection 
colletion.delete_one({'name': 'person1'})
colletion.delete_many({'name': 'person1'})

#delete_collection ลบ collection
db.drop_collection('<collection_name>'
"""