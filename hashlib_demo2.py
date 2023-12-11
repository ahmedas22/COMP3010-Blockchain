import hashlib


# genesis
m = hashlib.sha256()
m.update('Prof!'.encode())
m.update('3010 rocks'.encode()) 
m.update('Warning:'.encode()) 
m.update('Procrastinators'.encode()) 
m.update('will be sent back'.encode()) 
m.update('in time to start'.encode()) 
m.update('early.'.encode()) 
timestamp = int(1699293749)
m.update(timestamp.to_bytes(8, 'big')) # when
m.update('742463477029129'.encode()) # nonce
print('5b0cc813303f305927dbaf559bebab19229ba30106687a61ed4c62d000000000') # should be
print(m.hexdigest()) # is

#next block
m = hashlib.sha256()
m.update('5b0cc813303f305927dbaf559bebab19229ba30106687a61ed4c62d000000000'.encode())
m.update('Prof!'.encode())
m.update('ramifies'.encode())
m.update("marzipan's".encode())
m.update("gravels".encode())
m.update("Dakotan's".encode())
m.update('Dean'.encode())
m.update(int(1699295268).to_bytes(8,'big'))
m.update('2251755442'.encode())

print('c52368025ea9253b9d4371ebec8e271f214779c18bc123a21dd8ef5f00000000')
print(m.hexdigest())
