class WorldPartition():
    """
    Class for the world partition of the map.

    Info:
        A world partition is a partition of the map into squares in order to speed up the search for points.
    """

    def __init__(self, size: int = 100, partition_size: int = 10):
        """
        Initializes the world partition.

        Args:
            size: Size of the map.
            partition_size: Size of the partitions.
        """

        self.size = size
        self.partition_size = partition_size
        self.world_partition = self.create_world_partition()

    def get_world_partition(self, start_point, points_needed, clumping = 1):
        """
        Gets the world partition of the map.

        Args:
            start_point: Starting point of the world partition.
            points_needed: Number of points needed to be found for the world partition.
            clumping: Clumping of the world partition.
        """
        # v1 = np.log(points_needed)
        # v2 = np.log(self.partition_size)
        
        # distance = int(v1/v2)

        distance = int((((points_needed/100)**(1/2) + 1) // 2) + 1)
        distance = min(distance, self.size//self.partition_size)
        distance += clumping//10
        distance += 2
        # Gets the sets of points within the distance square of the start point
        sets = [self.world_partition[
                                    (start_point[0]//self.partition_size+i,
                                       start_point[1]//self.partition_size+j)
                                       ] 
                            for i in range(-distance, distance+1) 
                            for j in range(-distance, distance+1)
                            if (start_point[0]//self.partition_size+i,
                                start_point[1]//self.partition_size+j) in self.world_partition
                ]
    
        return sets
    
    def create_world_partition(self):
        """
        Creates the world partition of the map.
        
        Args:
            start_point: Starting point of the world partition.
            points_needed: Number of points needed to be found for the world partition.
        """

        rows = self.size // self.partition_size
        cols = self.size // self.partition_size

        partition = dict()

        for i in range(self.size):
            for j in range(self.size):
                if (i//self.partition_size, j//self.partition_size) in partition:
                    partition[(i//self.partition_size, j//self.partition_size)].add((i,j))
                else:
                    partition[(i//self.partition_size, j//self.partition_size)] = {(i,j)}
        
        return partition
        
