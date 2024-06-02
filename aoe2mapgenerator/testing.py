import time
import sys



def awesome_function(n: int):
    cool_list = []

    start_time = time.time()  # Start the timer

    for i in range(n):
        cool_list.append(i)

    end_time = time.time()  # Stop the timer

    elapsed_time = end_time - start_time
    print("Elapsed time:", elapsed_time, "seconds")

if __name__=="__main__":
    awesome_function(int(sys.argv[1]))