"""Small deterministic monogram icons; no font or network dependency."""
import struct
import zlib

GLYPHS={'student':['01110','10001','10000','01110','00001','10001','01110'],
        'guardian':['01110','10001','10000','10111','10001','10001','01110']}


def icon(role,size):
    color=(23,99,88) if role=='student' else (35,56,65)
    rows=[]
    for y in range(size):
        row=bytearray([0])
        for x in range(size):
            # Rounded flat tile and a white S/G monogram.
            nx,ny=(x+.5)/size,(y+.5)/size
            rounded=(max(abs(nx-.5)-.34,0)**2+max(abs(ny-.5)-.34,0)**2)<=.15**2
            gx,gy=int((nx-.25)*10),int((ny-.15)*10)
            letter=0<=gx<5 and 0<=gy<7 and .25<=nx<.75 and .15<=ny<.85 and GLYPHS[role][gy][gx]=='1'
            row.extend((*((255,255,255) if letter else color),255 if rounded else 0))
        rows.append(bytes(row))
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
