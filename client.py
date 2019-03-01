################################################################################
import threading
import time
import socket
import sys
from PIL import Image
import io
import os
import os.path
import re
from multiprocessing import Lock
# for separating path and url
from urllib.parse import urlparse
#######################################################################################
                    # GLOBAL
#######################################################################################
CHUNK_SIZE = 4096
Exists=False
old_size=0 # file size of existing file 
mutex = Lock()
port = 80  # web
threads = []
reply =[] # saving bytes downloaded by each thread
no_of_threads=int(sys.argv[2])
ranges=[]
resume=False
if(sys.argv[3]=="resume"):
 resume=True


#########################################################################################
    #PARSING URL
#########################################################################################
URLparser = urlparse(str(sys.argv[1]))

path=str(URLparser.path)
host=str(URLparser.netloc)
# name of file to sivee
File_to_save=os.path.basename(path)
if(str(host).find("localhost")>-1):
   host='localhost'
   port=8080







#################################################################################################
# this function makes ranges for request
def make_ranges(start,no_of_threads,file_size):
    
    thread_chunk=int(file_size/no_of_threads)
    
   
   
    for i in range(no_of_threads):
        
        ran = str(start+1)+"-"+str((start+thread_chunk) if i!=no_of_threads-1 else lastbyte-1)
        ranges.insert(i, ran)
        
        start=start+thread_chunk
        
#################################################################################################
# this request header to get the file size to be downloaded
def get_content_size():
    request = "HEAD /"+ path +" HTTP/1.0\r\nHost: "+host+" \r\n\r\n"
    responce = create_socket(request)
    data = responce
    CRLF = b"\r\n\r\n"
    splitted = data.split(CRLF, 1)
    headers = splitted[0].decode()
    request_line = headers.split('\n')[0]
    response_code = request_line.split()[1]
    headers = headers.replace(request_line, '')
    p = "Content-Length: (\d+)"
    m  = re.search(p,headers)
    contentLen = int(m.group(1))
    return(contentLen)
 #################################################################################################   
# recieve and combine chunks of a file
def complete_chunks_receive(sock, chunk_size=CHUNK_SIZE):
    '''
    Gather all the data from a request.
    '''
    chunks = []
    while True:
        chunk = sock.recv(int(chunk_size))
        if chunk:
            chunks.append(chunk)
        else:
            break

    return b''.join(chunks)

#################################################################################################
# create socket
def create_socket(request):
      
   # print('# Creating socket')
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('Failed to create socket')
        sys.exit()

   # print('# Getting remote IP address') 
    try:
        remote_ip = socket.gethostbyname( host )
    except socket.gaierror:
        print('Hostname could not be resolved. Exiting')
        sys.exit()

    # Connect to remote server
  #  print('# Connecting to server, ' + host + ' (' + remote_ip + ')')
    s.connect((remote_ip , port))

    # Send data to remote server
    #print('# Sending data to server')
   
    try:
        s.sendall(request.encode())
    except socket.error:
        print('Send failed')
        sys.exit()

    # Receive data
   # print('# Receive data from server')
    res = complete_chunks_receive(s,4096)
    return (res)
#################################################################################################
#write to file from array
def write_to_file():
 f = open('downloaded/'+File_to_save, 'wb+')
 for temp in reply:
     f.write(temp)

 f.close()

#################################################################################################
def req_responce(index,ran):
   
    start_time = time.time()
  # get request for each thread

    request ="GET /"+ path +" HTTP/1.0\r\nHost: "+host+" \r\nRange: bytes="+ran+" \r\n\r\n"
    res= create_socket(request)
    
    CRLF = b"\r\n\r\n"
    splitted = res.split(CRLF, 1)
    headers = splitted[0].decode()
    request_line = headers.split('\n')[0]
    response_code = request_line.split()[1]
    headers = headers.replace(request_line, '')
    # extracting the body from the responce
    body = res.replace(headers.encode(), b'').replace(request_line.encode(), b'').replace(CRLF,b'')
    
    with mutex:
     reply.insert(index,body)

    bytess=len(body)
   
    print("thread : "+str(index)+" downloaded "+str(bytess) +" bytes at %.2f KB/s "%(bytess/((time.time() - start_time)*1024)))
   

######################################################################################################    
 
# makes threads and pas ranges with thread for connections
def download():
    if not Exists:
        make_ranges(-1,no_of_threads,size)
    else :
        make_ranges(old_size-1,no_of_threads,lastbyte-old_size)   
        
    for i in range(no_of_threads):
        t = threading.Thread(target=req_responce, args=(i,ranges[i],))
        threads.append(t)
        t.start()

        
    for t in threads:
        t.join()
    write_to_file()
######################################################################################################



#######################################################################################################
                # main
#######################################################################################################
lastbyte=get_content_size()  
size=lastbyte
filepath=os.path.join('downloaded',File_to_save)
exists =os.path.isfile(filepath)

if exists and resume:
    Exists=True
    old_size=os.path.getsize(filepath)
  
    
    if(lastbyte<=old_size):
        print("file already complete downloaded")
        sys.exit()
    elif(lastbyte>old_size):
        print("resuming download")
        download()
else:
     download()
####################################################################################################