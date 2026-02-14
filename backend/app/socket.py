from socketio import AsyncServer

sio = None


def get_sio() -> AsyncServer:
    """Get the Socket.IO server instance"""
    return sio


def set_sio(server: AsyncServer):
    """Set the Socket.IO server instance"""
    global sio
    sio = server
