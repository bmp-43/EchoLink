from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key_123"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ''.join(random.choices(ascii_uppercase, k=length))
        if code not in rooms:
            return code  # <- Moved return here






@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        session.clear()  
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join")
        create = request.form.get("create")

        if not name:
            session['error'] = "Please enter your name!"  
            return redirect(url_for("home"))              

        if join and not code:
            session['error'] = "Please enter the room code!"  
            return redirect(url_for("home"))                  

        room = code

        if create:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
            print(f"[INFO] Created room {room} for {name}")
        elif code not in rooms:
            session['error'] = "Room does not exist!" 
            return redirect(url_for("home"))           

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    error = session.pop("error", None)
    return render_template("home.html", error=error)


@app.route('/room')

def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for ('home'))

    return render_template("room.html", room=room, name=session.get("name"))

@socketio.on("message")

def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
    
    if room not in rooms:
        rooms[room] = {"members": 0, "messages": []}
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    send({"name": name, "message": "has left the room"}, to=room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0',debug=True)
