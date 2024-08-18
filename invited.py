from datetime import datetime, timedelta
import re
import socket
import struct
import requests
import urllib3
import json
from time import sleep
from numpy import uint16, uint32, uint64
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import threading
import datetime
import time
import random
from random import randint
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
import threading
u16 = uint16
u32 = uint32
u64 = uint64
urllib3.disable_warnings()
VERSION_HASH = "2288b5adc1b3377c217c9e212e024300"


def busy_wait(duration):
    start_time = time.time()
    while (time.time() - start_time) < duration:
        pass


class BStream:
    def __init__(self, data=b"", endianess="big"):
        self.data = data
        self.position = 0
        self.endianess = endianess

    def read_utf(self):
        return self.read_bytes(self.read_short()).decode("utf-8")

    def read_any_integer(self, size):
        return int.from_bytes(self.read_bytes(size), self.endianess)

    def read_byte(self):
        return self.read_any_integer(1)

    def read_short(self):
        return u16(self.read_any_integer(2))

    def read_3int(self):
        return u32(self.read_any_integer(3))

    def read_int(self):
        return u32(self.read_any_integer(4))

    def read_long(self):
        return u64(self.read_any_integer(8))

    def read_double(self):
        if self.endianess == "little":
            return struct.unpack("<d", self.read_bytes(8))
        else:
            return struct.unpack(">d", self.read_bytes(8))

    def read_float(self):
        if self.endianess == "little":
            return struct.unpack("<f", self.read_bytes(4))
        else:
            return struct.unpack(">f", self.read_bytes(4))

    def read_bytes(self, size):
        bs = self.data[self.position:self.position + size]
        self.position += size
        return bs

    def write_utf(self, s):
        self.write_short(len(s))
        self.write_bytes(s.encode("utf-8"))

    def write_bytes(self, data):
        self.data += data
        self.position += len(data)

    def write_any_integer(self, n, size):
        n = int(n)  # cast numpy ints
        self.data += n.to_bytes(size, self.endianess)
        self.position += size

    def write_byte(self, n):
        self.write_any_integer(n, 1)

    # def write_short(self, n):
    #    self.write_any_integer(n, 2)
    def write_short(self, n):
        if n < 0:
            n = n + 2**16
        self.write_any_integer(n, 2)

    def write_3int(self, n):
        self.write_any_integer(n, 3)

    def write_int(self, n):
        self.write_any_integer(n, 4)

    def write_long(self, n):
        self.write_any_integer(n, 8)

    def write_double(self, value):
        if self.endianess == "little":
            return self.write_bytes(struct.unpack("<d", value))
        else:
            return self.write_bytes(struct.unpack(">d", value))

    def write_float(self, value):
        if self.endianess == "little":
            return self.write_bytes(struct.pack("<f", value))
        else:
            return self.write_bytes(struct.unpack(">f", value))


class Get_dosid:
    def __init__(self):
        pass

    def get_dosid(self, username, password):
        response = requests.get("https://www.darkorbit.com/")
        main_page = response.text
        soup = BeautifulSoup(main_page, 'html.parser')
        form = soup.find('form', {'name': 'bgcdw_login_form'})
        action = form['action']
        response = requests.post(
            action, data={'username': username, 'password': password})

        server = None
        dosid = None
        for cookie in response.cookies:
            if cookie.name == 'dosid':
                dosid = cookie.value
            if 'int' in cookie.domain:
                server = cookie.domain
                server = server.replace('.darkorbit.com', '')
        return dosid, server


class Module:
    def __init__(self):
        pass

    def read(stream):
        pass

    def write(stream):
        pass


class VersionRequest:
    def __init__(self, version_hash):
        self.hash = version_hash

    ID = 666

    def write(self, stream):
        stream.write_short(self.ID)
        stream.write_utf(self.hash)


class LoginRequest:
    def __init__(self, user_id, faction_id, session_id, version, instance_id, unk=False):
        self.user_id = u32(user_id)
        self.faction_id = u32(faction_id)
        self.session_id = session_id
        self.version = version
        self.instance_id = u32(instance_id)
        self.unk = unk

    ID = 7

    def write(self, stream):
        stream.write_short(self.ID)
        stream.write_int(self.user_id << u32(3) % u32(
            32) | self.user_id >> u32(32) - u32(3) % u32(32))
        stream.write_short(u32(65535) & ((u32(65535) & self.faction_id) >> u32(
            9) % u32(16) | (u32(65535) & self.faction_id) << u32(16) - u32(9) % u32(16)))
        stream.write_utf(self.session_id)
        stream.write_utf(self.version)
        stream.write_int(self.instance_id << u32(12) % u32(
            32) | self.instance_id >> u32(32) - u32(12) % u32(32))
        stream.write_byte(u32(1))

class InitPacket:
    def __init__(self, key, number):
        self._s16 = key
        self._J1a = u32(number)

    ID = 14

    def write(self, stream):
        stream.write_short(self.ID)
        stream.write_utf(self._s16)
        stream.write_short(self._J1a)


class KeepAlive:
    def __init__(self):
        pass

    ID = 2

    def write(self, stream):
        # print("KeepAlive")
        stream.write_short(self.ID)

class ClaimVIPModule:
    def __init__(self,loot_id):
        self.loot_id = loot_id

    ID = 15275

    def write(self, stream):
        stream.write_utf(self.loot_id)

class Invite:
    def __init__(self, name):
        self.name = name

    ID = -11173

    def write(self, stream):
        stream.write_short(self.ID)
        encoded_name = self.name.encode('utf-8')
        stream.write_short(len(encoded_name))
        stream.write_bytes(encoded_name)


class CancelInvite:
    def __init__(self, uid):
        self.uid = uid

    ID = -24695

    def write(self, stream):
        stream.write_short(self.ID)
        modified_uid = ((self.uid << 8) & 0xFFFFFFFF) | (self.uid >> 24)
        stream.write_int(modified_uid)


class LeaveGroup:
    def __init__(self):
        pass

    ID = 9875

    def write(self, stream):
        stream.write_short(self.ID)


class OtherPlayerPosInfo:
    def __init__(self):
        pass

    ID = 90

    def read(self, stream):
        self.user_id = stream.read_int()
        self.user_id = ((self.user_id << 16) & 0xFFFFFFFF) | (
            self.user_id >> 16)

        self.x_encoded = stream.read_int()
        self.x = (self.x_encoded >> 13) | (self.x_encoded << 19) & 0xFFFFFFFF

        self.y = stream.read_int()
        self.y = ((self.y << 16) & 0xFFFFFFFF) | (self.y >> 16)

        self.w5u = stream.read_int()
        self.w5u = ((self.w5u << 14) & 0xFFFFFFFF) | (self.w5u >> 18)


class OtherPlayerInfo:
    def __init__(self):
        pass

    ID = 83

    def read(self, stream):
        self.user_id = stream.read_int()
        self.user_id = ((self.user_id >> 15) & 0xFFFFFFFF) | (
            self.user_id << 17) & 0xFFFFFFFF
        self.type_id = stream.read_utf()
        self.u2Q = stream.read_int()
        self.u2Q = ((self.u2Q >> 8) & 0xFFFFFFFF) | (
            self.u2Q << 24) & 0xFFFFFFFF
        self.clan_tag = stream.read_utf()
        self.user_name = stream.read_utf()
        self.x = stream.read_int()
        self.x = ((self.x >> 6) & 0xFFFFFFFF) | (self.x << 26) & 0xFFFFFFFF
        self.y = stream.read_int()
        self.y = ((self.y >> 15) & 0xFFFFFFFF) | (self.y << 17) & 0xFFFFFFFF
        self.faction_id = stream.read_int()
        self.faction_id = ((self.faction_id >> 1) & 0xFFFFFFFF) | (
            self.faction_id << 31) & 0xFFFFFFFF
        self.u5B = stream.read_int()
        self.u5B = ((self.u5B >> 15) & 0xFFFFFFFF) | (
            self.u5B << 17) & 0xFFFFFFFF
        self.c4j = stream.read_int()
        self.c4j = ((self.c4j >> 1) & 0xFFFFFFFF) | (
            self.c4j << 31) & 0xFFFFFFFF
        self.y5k = stream.read_byte()
        self.MF = stream.read_byte()  # Assuming this reads an object from the stream
        self.W39 = stream.read_int()
        self.W39 = ((self.W39 >> 12) & 0xFFFFFFFF) | (
            self.W39 << 20) & 0xFFFFFFFF
        self.q12 = stream.read_byte()
        self.npc = stream.read_byte()
        self.cloaked = stream.read_byte()
        self.E4E = stream.read_int()
        self.E4E = ((self.E4E >> 10) & 0xFFFFFFFF) | (
            self.E4E << 22) & 0xFFFFFFFF
        self._14r = stream.read_int()
        self._14r = ((self._14r >> 1) & 0xFFFFFFFF) | (
            self._14r << 31) & 0xFFFFFFFF
        self._13n = stream.read_utf()
        self.modifier_length = stream.read_byte()
        # Assuming this reads an object from the stream
        self.modifier = [stream.read_byte()
                         for _ in range(self.modifier_length)]
        self.p1i = stream.read_byte()  # Assuming this reads an object from the stream


class Jump:
    def __init__(self, mapId, gate_id):
        self.mapId = mapId  # new x
        self.gate_id = gate_id  # current x

    ID = 19

    def write(self, stream):
        stream.write_int(self.mapId >> 7 | self.mapId << 25)
        stream.write_int(self.gate_id >> 6 | self.gate_id << 26)


class Movement:
    def __init__(self, _p27, _k4F, _S2S, _v4W):
        self._p27 = _p27  # new x
        self._k4F = _k4F  # current x
        self._S2S = _S2S  # new y
        self._v4W = _v4W  # current y

    ID = 82

    def write(self, stream):
        stream.write_short(self.ID)
        stream.write_int(self._k4F << 11 | self._k4F >> 21)
        stream.write_int(self._v4W >> 15 | self._v4W << 17)
        stream.write_int(self._p27 << 13 | self._p27 >> 19)
        stream.write_int(self._S2S << 10 | self._S2S >> 22)

# Create and send the custom packet


class ShipSelect:
    def __init__(self, ship_id):
        self.ship_id = ship_id

    ID = 165

    def write(self, stream):
        stream.write_short(self.ID)
        stream.write_int(self.ship_id)
    # "_-v4W": 6374, x pos
    # "_-p27": 16742, y pos
    # "_-03u": 604,
    # "_-l4Q": 150200589, # uid npc
    # "_-Y55": 221,
    # "radius": 55,
    # "_-H48": 591,
    # "_-c3S": 206


class InviteError:
    def __init__(self):
        pass

    ID = -30928

    def read(self, stream):
        self.error = stream.read_short()


class Dispatch:
    def __init__(self, dispatch_id):
        self.dispatch_id = dispatch_id

    ID = 16428

    def write(self, stream):
        stream.write_short(self.ID)
        stream.write_int(self.dispatch_id >> 1 | self.dispatch_id << 31)


class GateInit:
    def __init__(self):
        self.unknown_list = []
        pass

    ID = 3389

    def read(self, stream):
        loc4_ = 0
        self.id = stream.read_int()
        self.id = self.id >> u32(10) % u32(
            32) | self.id << u32(32) - u32(10) % u32(32)
        self.factionId = stream.read_int()
        self.factionId = self.factionId << u32(2) % u32(
            32) | self.factionId >> u32(32) - u32(2) % u32(32)
        self.type = stream.read_int()
        self.type = self.type << u32(15) % u32(
            32) | self.type >> u32(32) - u32(15) % u32(32)
        self.x = stream.read_int()
        self.x = self.x >> u32(11) % u32(
            32) | self.x << u32(32) - u32(11) % u32(32)
        self.y = stream.read_int()
        self.y = self.y >> u32(9) % u32(
            32) | self.y << u32(32) - u32(9) % u32(32)
        self.bool_a = stream.read_byte()
        self.bool_b = stream.read_byte()
        if len(self.unknown_list) > 0:
            self.unknown_list.clear()

        _loc2_ = 0
        _loc3_ = stream.read_byte()
        while (_loc2_ < _loc3_):
            _loc4_ = stream.read_int()
            _loc4_ = _loc4_ << u32(2) % u32(
                32) | _loc4_ >> u32(32) - u32(2) % u32(32)
            self.unknown_list.append(_loc4_)
            _loc2_ += 1


class UpdateModifier:
    def __init__(self):
        pass

    ID = 280

    def read(self, stream):
        self.userId = stream.read_int()
        self.userId = self.userId >> u32(12) % u32(
            32) | self.userId << u32(32) - u32(12) % u32(32)
        self.modifier = stream.read_short()
        self.attribute = stream.read_int()
        self.attribute = self.attribute << u32(7) % u32(
            32) | self.attribute >> u32(32) - u32(7) % u32(32)
        self.name = stream.read_utf()
        self.count = stream.read_int()
        self.count = self.count >> u32(14) % u32(
            32) | self.count << u32(32) - u32(14) % u32(32)
        self.activated = stream.read_byte()


class HeroInit:
    def __init__(self):
        self.modifiers = []
        pass

    ID = 49

    def read(self, stream):
        _loc4_ = UpdateModifier()
        self.userId = stream.read_int()
        self.userId = self.userId >> u32(14) % u32(
            32) | self.userId << u32(32) - u32(14) % u32(32)
        self.userName = stream.read_utf()
        self.typeId = stream.read_utf()
        self.speed = stream.read_int()
        self.speed = self.speed << u32(12) % u32(
            32) | self.speed >> u32(32) - u32(12) % u32(32)
        self.shield = stream.read_int()
        self.shield = self.shield << u32(14) % u32(
            32) | self.shield >> u32(32) - u32(14) % u32(32)
        self.max_shield = stream.read_int()
        self.max_shield = self.max_shield << u32(13) % u32(
            32) | self.max_shield >> u32(32) - u32(13) % u32(32)
        self.hp = stream.read_int()
        self.hp = self.hp << u32(9) % u32(
            32) | self.hp >> u32(32) - u32(9) % u32(32)
        self.max_hp = stream.read_int()
        self.max_hp = self.max_hp << u32(15) % u32(
            32) | self.max_hp >> u32(32) - u32(15) % u32(32)
        self.cargo_left = stream.read_int()
        self.cargo_left = self.cargo_left << u32(10) % u32(
            32) | self.cargo_left >> u32(32) - u32(10) % u32(32)
        self.cargo_size = stream.read_int()
        self.cargo_size = self.cargo_size >> u32(14) % u32(
            32) | self.cargo_size << u32(32) - u32(14) % u32(32)
        self._03V = stream.read_int()
        self._03V = self._03V >> u32(11) % u32(
            32) | self._03V << u32(32) - u32(11) % u32(32)
        self._3p = stream.read_int()
        self._3p = self._3p >> u32(15) % u32(
            32) | self._3p << u32(32) - u32(15) % u32(32)
        self.x = stream.read_int()
        self.x = self.x >> u32(14) % u32(
            32) | self.x << u32(32) - u32(14) % u32(32)
        self.y = stream.read_int()
        self.y = self.y >> u32(4) % u32(
            32) | self.y << u32(32) - u32(4) % u32(32)
        self.mapId = stream.read_int()
        self.mapId = self.mapId << u32(11) % u32(
            32) | self.mapId >> u32(32) - u32(11) % u32(32)
        self.factionId = stream.read_int()
        self.factionId = self.factionId << u32(5) % u32(
            32) | self.factionId >> u32(32) - u32(5) % u32(32)
        self._04t = stream.read_int()
        self._04t = self._04t >> u32(3) % u32(
            32) | self._04t << u32(32) - u32(3) % u32(32)
        self._r3E = stream.read_int()
        self._r3E = self._r3E >> u32(5) % u32(
            32) | self._r3E << u32(32) - u32(5) % u32(32)
        self.premium = stream.read_byte()
        self.experience = stream.read_double()
        self.honours = stream.read_double()
        self.level = stream.read_int()
        self.level = self.level >> u32(15) % u32(
            32) | self.level << u32(32) - u32(15) % u32(32)
        self.credits = stream.read_double()
        self.uridium = stream.read_double()
        self.jackpot = stream.read_float()
        self._cu = stream.read_int()
        self._cu = self._cu << u32(14) % u32(
            32) | self._cu >> u32(32) - u32(14) % u32(32)
        self.clanTag = stream.read_utf()
        self._t4O = stream.read_int()
        self._t4O = self._t4O << u32(5) % u32(
            32) | self._t4O >> u32(32) - u32(5) % u32(32)
        self._b23 = stream.read_byte()
        self.cloaked = stream.read_byte()
        self._Hd = stream.read_byte()
        _loc2_ = u32(0)
        _loc3_ = u32(0)
        if len(self.modifiers) == 0:
            self.modifiers = []
        _loc2_ = u32(0)
        _loc3_ = stream.read_byte()
        while (_loc2_ < _loc3_):
            stream.read_short()  # type ignored
            _loc4_.read(stream)
            self.modifiers.append(_loc4_)
            _loc2_ += 1


class Gameclient:
    def __init__(self, sid, server):

        self.sesh = requests.session()
        self.sesh.headers = {
            'User-Agent': 'BigPointClient/1.6.9',
        }
        self.running = False
        self.sid = sid
        self.server = server
        self.ip = None
        self.sock = None
        self.last_x = 0  # Initialize with default values
        self.last_y = 0  # Initialize with default values
        self.vip_modules = ["equipment_shipupgrade_dmg-xt10", "equipment_shipupgrade_hp-xt10", "equipment_shipupgrade_spc-xt10"]
    def get_ip(self, map_id):
        response = self.sesh.get(f"https://{self.server}.darkorbit.com/spacemap/xml/maps.php", verify=False)
        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code.

        # Parse the XML response
        root = ET.fromstring(response.text)

        # Find the map element with the given id
        map_element = root.find(f"./map[@id='{map_id}']")

        if map_element is not None:
            # Extract the gameserverIP text
            gameserver_ip = map_element.find('gameserverIP').text
            gameserver_ip, port = gameserver_ip.split(":")
            print(f"Found map with id {map_id} and gameserverIP {gameserver_ip}, port {port}")

            return gameserver_ip, port
        else:
            raise ValueError(f"No map found with id {map_id}")

    def login(self):
        self.sesh.cookies.set(
            'dosid', self.sid, domain=f"{self.server}.darkorbit.com", path='/')

        try:
            r = self.sesh.get(
                f"https://{self.server}.darkorbit.com/indexInternal.es?action=internalMapRevolution")
            self.flashvars = json.loads(
                re.findall("({\"lang\":.*?})\)", r.text)[0])
            self.pid = self.flashvars["pid"]
        except Exception as e:
            print(e)
            print("Login failed")
            exit(-1)
        pass

    def connect(self):
        self.ip,port = self.get_ip(self.flashvars["mapID"])
        port = int(port)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.connect((self.ip, port))

    def send_packet(self, packet):
        out = BStream()
        packet.write(out)
        out = struct.pack(">bh", (len(out.data) & 0xff0000) >>
                          16, len(out.data) & 0xffff) + out.data
        self.sock.send(out)

    def random_movement(self):
        while self.running:
            # eic
            #x = randint(17800, 18000)
            #y = 1200
            # vru
            x = randint(19500, 19200)
            y = 12800
            # mmo
            #x = randint(17800, 18000)
            #y = 1200
            self.send_packet(Movement(x, self.last_x, y, self.last_y))
            self.last_x = x
            self.last_y = y
            sleep(1)
    
    def invite_and_cancel(self):
        while self.running:
            if len(user_data) > 0:
                for username, id in user_data.items():
                    self.send_packet(Invite(username))
                    print(f"[*] Invited {username}")
                    busy_wait(time_pause)
                    self.send_packet(CancelInvite(id))
                    print(f"[*] Canceled invite {username}")
            else:
                busy_wait(1)

    def run(self):
        dispatch = False
        if not self.flashvars:
            raise Exception("[!] Not logged in")

        last_x = None
        last_y = None

        self.connect()
        self.sock.send(b"\0")
        self.send_packet(VersionRequest(VERSION_HASH))

        self.running = True
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.invite_and_cancel, id='invite_and_cancel')
        scheduler.add_job(self.random_movement, id='movement')
        scheduler.add_job(self.send_packet, 'interval', args=[
                          KeepAlive()], seconds=5, id='keep_alive')
        scheduler.add_job(self.send_packet, 'interval', args=[
                          LeaveGroup()], seconds=2, id='leave_group')
        scheduler.start()
        while self.running:

            # read packet length
            bs = BStream(self.sock.recv(3))
            packet_len = bs.read_3int()

            # read packet contents
            bs = BStream()
            while bs.position < packet_len:
                bs.write_bytes(self.sock.recv(packet_len - bs.position))
            bs.position = 0

            packet_id = bs.read_short()

            # Handle packets
            if packet_id == 667:
                print("[*] Got version response, hash: {}".format(bs.read_utf()))
                login_req = LoginRequest(
                    self.flashvars["userID"], 0, self.flashvars["sessionID"], "", self.flashvars["pid"])
                self.send_packet(login_req)
            elif packet_id == HeroInit.ID:
                heroinit = HeroInit()
                heroinit.read(bs)
                # print("HeroInit x: {} y: {}".format(heroinit.x, heroinit.y))
                self.last_x = heroinit.x
                self.last_y = heroinit.y

                # print(f"[*] Hero init {heroinit.userName} {heroinit.userId} {heroinit.experience}")

                # Need to send this otherwise the server will stop responding
                init_thing = "3D 1918x1041 .root1.instance470.MainClientApplication0.ApplicationSkin2.Group3.Group4._-Q53_5.instance25058 root1 false -1"
                self.send_packet(InitPacket(init_thing, 1))
                self.send_packet(InitPacket(init_thing, 2))
                self.send_packet(KeepAlive())
            elif packet_id == GateInit.ID:
                gate_packet = GateInit()
                gate_packet.read(bs)
                # print(f"[*] Gate init {gate_packet.id} {gate_packet.x} {gate_packet.y}")
            elif packet_id == 1:
                # print("[*] Message packet", bs.read_utf())
                pass
            elif packet_id == 0:
                print("[*] connection closed")
                break
            elif packet_id == 90:
                other_player_pos = OtherPlayerPosInfo()
                other_player_pos.read(bs)
                print(
                    f"[*] Other player pos {other_player_pos.user_id} {other_player_pos.x} {other_player_pos.y}")
            else:
                #print("[*] Unknown packet [{}]: {}".format(packet_id, bs.data.hex()))
                pass


global name
global id
global time_pause
user_data = {"NotㅤJessiㅤツ": 96691059}
time_pause = 0.000001

dosids = ["13cee505f541f443bcaf29339188dfdb"]

def run_client(dosid):
    client = Gameclient(dosid, 'tr5')
    client.login()
    client.run()
run_client(dosids[0])
