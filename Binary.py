import matplotlib.pyplot as plt
def make_bin(num):
    if num == 0:
        return '0'
    bin_representation = ''
    power = 1
    while power <= num:
        power *= 2
    power //= 2 

    while power > 0:
        if num >= power:
            num -= power
            bin_representation += '1'
        else:
            bin_representation += '0'
        power //= 2
    
    return bin_representation
def find_bin(num):
    num = list(num)
    num1 = 0
    new = len(num)
    while new != 0:
        if num[0] == "1":
            num1 += 2**(new)
        num.pop(0)
        new = len(num)
    return int(num1/2)
def subnet(hosts, nets):
    subhost = hosts
    hosts = hosts * nets + 2
    netwrk = 0
    num = 0
    data_points = []
    for i in range(nets):
        if i+1 == 1:
            print(f"\n{i+1}st Subnet Network: .{netwrk} Broadcast: .{netwrk+subhost+1}")
        elif i+1 == 2:
            print(f"\n{i+1}nd Subnet Network: .{netwrk} Broadcast: .{netwrk+subhost+1}")
        elif i+1 == 3:
            print(f"\n{i+1}rd Subnet Network: .{netwrk} Broadcast: .{netwrk+subhost+1}")
        else:
            print(f"\n{i+1}th Subnet Network: .{netwrk} Broadcast: .{netwrk+subhost+1}")
        netwrk += subhost+2
        for i in range(subhost):
            num += 1
            print(f".{num}", end=" ")
            data_points.append((i+1, num))
        num += 2
    hosts = netwrk
    print(f"\n{hosts} Hosts needed.")
    if hosts >= 255:
        return "Error: Cannot create subnet with more than 255 hosts"
    binary = make_bin(hosts)
    bbn = len(binary)
    for i in range(bbn):
        if binary[i] == "1":
            binary = "1"
            for i in range(bbn):
                binary += "0"
            break
    ones = 7 - bbn
    v4 = '1'*ones + binary
    print(f"11111111  11111111  11111111  {v4}")
    print(f"255       255       255       0-{find_bin(binary)}   ")
    broadcast = find_bin(binary)
    tot = (nets * subhost)
    binary = find_bin(binary)

    plot_graph(data_points)
    return binary
def plot_graph(data_points):
    x, y = zip(*data_points)  # Unpack data points into x (subnets) and y (hosts)
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, c='blue', label="Hosts per Subnet")
    plt.title("Combinations of Hosts and Subnets")
    plt.xlabel("# of subnets Number")
    plt.ylabel("Host Number")
    plt.legend()
    plt.grid(True)
    plt.show()
def use():
    user = input("Binary to number (B), Number to binary (N), or Subnet (S): ").lower()
    if user == "s":
        nets = int(input("# of subnets: "))
        hosts = int(input("Hosts per subnet: "))
        num = subnet(hosts, nets)
        print(f"/{num}")
    elif user == "n":
        num = int(input("Enter a number: "))
        binary = make_bin(num)
        print(f"{binary}")
    elif user == "b":
        num = input("Enter a binary number: ")
        print(f"{find_bin(num)}")
    else:
        print("Invalid input")
        use()
    user = input("Keep going? (y/n): ").lower()
    if user == "y":
        use()
    else:
        print("Goodbye!")
use()