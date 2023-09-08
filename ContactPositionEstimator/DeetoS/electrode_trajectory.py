import SimpleITK as sitk
from numpy import array,zeros,float64,sum,empty,mean
from numpy.linalg import norm

from image_tools import *

class ElectrodeTrajectoryConstructor():
    
    CONTACTS_DIST = 3.5
    MIN_REGION_SIZE = 3
    MAX_REGION_SIZE = 10

    def _compute_threshold(self,itk_image):
        image = sitk.GetArrayFromImage(itk_image)
        image = image[image!=0].ravel()
        return sorted(image)[int(len(image)*0.45)]

    def __init__(self, nii_gz_path,image_intensity_threshold=None):
        '''
        Reads the image CT passed as string, the CT can be either compressed or uncompressed\n
        then computes the intensity threshold of the image if not provided as parameter.\n
        Then sets some auxiliary vectors.
        '''
        #self._image = imread(nii_gz_path,US)
        #print(sitk.ReadImage(nii_gz_path,sitk.sitkUInt32).GetSize())
        image = sitk.ReadImage(nii_gz_path,sitk.sitkUInt32)
        #self._image_array = array_from_image(self._image)

        if image_intensity_threshold is None:
            self._threshold = self._compute_threshold(image)
        else:
            self._threshold = image_intensity_threshold
        self._zero_vect = zeros(len(image.GetSize()),dtype=int)
        self._size_vect = array(image.GetSize(),dtype=int)
        self._clipping_borders = (self._zero_vect,self._size_vect)
        self._image = image
        self._electrode = None
        self._PhysToIndx = image.TransformPhysicalPointToIndex
        self._IndxToPhys = image.TransformIndexToPhysicalPoint 

    def _compute_center_of_gravity(self,image,cohords_offsets):
        '''
        calculates center of gravity of the image provided
        should work with images of any dimension

        Returns
        --------
                
        the center of gravity if the mass is not zero, otherwise returns None
        '''
        size_vect = array(image.GetSize(),dtype=int)
        m_Cg = zeros(len(size_vect),dtype=float)
        total_mass = 0
        for pixel_index_array in region_generator(tuple(self._zero_vect),max(size_vect),(self._zero_vect,size_vect),as_np_array=True):
            pixel_index_tuple = tuple(map(int,pixel_index_array))
            pixel_value = image[pixel_index_tuple]
            # double conversion of types is due to incompatibility between itk's and numpy's data types 
            m_Cg += array(self._IndxToPhys(tuple(map(int,pixel_index_array+cohords_offsets)))) * pixel_value
            total_mass += pixel_value
        if total_mass == 0:
            return None
        return m_Cg/total_mass

    def _get_point_with_highest_momentum(self,center_index,min_region_size,max_region_size):
        '''
        iterates from a min region size to a max region size and stops as soon as a center of gravity in the region is found
        '''
        img = self._image
        curr_region_size = min_region_size
        clipping_borders = self._clipping_borders
        first_iter = True
        # in original code this is a do while
        while curr_region_size < max_region_size or first_iter:
            first_iter = False
            region = get_squared_region(center_index,curr_region_size)
            if is_valid_region(region,clipping_borders):
                center_of_gravity = self._compute_center_of_gravity(img[region],tuple([slce.start for slce in region]))
                if center_of_gravity is None:
                    curr_region_size += 1
                else:
                    return center_of_gravity
            else:
                max_region_size -= 1
        return None

    def _get_region_value(self,pixel_index,region_size):
        '''
        returns the sum of every pixel value in this cubic region
        '''
        image = self._image
        clipping_borders = self._clipping_borders
        return sum([image[pixel_index_inner] for pixel_index_inner in region_generator(pixel_index,region_size,clipping_borders)])

    def _find_head(self,entry_point):
        '''
        iterates over a region around the entry point, finds the first pixel value 
        with pixel intensity above the threshold and with sum of pixel values within the min region that's above the threshold for the region size

        Returns
        ---------
        The head cohordinates as a tuple of floats or None if the head is not found
        '''
        img = self._image
        pixel_intensity_threshold = self._threshold
        min_region_size = self.MIN_REGION_SIZE
        max_region_size = self.MAX_REGION_SIZE
        center_index = self._PhysToIndx(entry_point)
        clipping_borders = self._clipping_borders
        for pixel_index in region_generator(center_index,max_region_size,clipping_borders):
            if img[pixel_index] > pixel_intensity_threshold and self._get_region_value(pixel_index,min_region_size) > min_region_size * pixel_intensity_threshold:
                return self._get_point_with_highest_momentum(pixel_index,min_region_size,max_region_size)
        return None

    def _get_next_point(self,p1,p2,p3,dist):
        '''
        returns the next point of the line represented by p1 and p2 which is also ```dist``` far from p2 in the direction of p3
        '''
        return p2 + (p3 - p2) * (norm(p1-p2)+dist) / norm(p2-p3)

    def _find_tail(self,head_point,target_point):
        '''
        given the head point and the target point finds the tail:
            - from the head finds the next point (p2) laying on the line to the target point at dist^2
            - from the p2 finds the point that's dist distant from p2 back to the head point
            - iterates 20 times the distance between one point and the next towards the target, picking always the point with highest momentum \n
            
        The algorithm terminates when one of the conditions below occurs:\n
            - (a) The difference between p3 and p2 is less than the lenght of a contact (meaning that the points are too close) 
            - (b) p3 has a ct value less than the threshold
            - (c) it is too far from the head point computed
            - (d) it is in the other emisphere.
        '''
        img = self._image
        pixel_value_threshold = self._threshold
        dist = self.CONTACTS_DIST
        min_region_size = self.MIN_REGION_SIZE; max_region_size = self.MAX_REGION_SIZE

        p2 = self._get_next_point(head_point,head_point,target_point,dist*2)
        p2 = self._get_point_with_highest_momentum(self._PhysToIndx(p2),min_region_size,max_region_size)
        if p2 is None:
            return None
        p3 = self._get_next_point(p2,head_point,p2,dist)
        p3 = self._get_point_with_highest_momentum(self._PhysToIndx(p3),min_region_size,min_region_size)
        for i in range(20):
            p1 = p2; p2 = p3
            p3 = self._get_next_point(p2,p1,p2,dist)
            p3 = self._get_point_with_highest_momentum(self._PhysToIndx(p3),min_region_size,min_region_size)
            if p3 is None:
                p3 = self._get_next_point(p2,p1,p2,dist)
                break
            if norm(p3-p2) < 2.5: #TODO ask for magic numbers
                break
            elif self._get_region_value(self._PhysToIndx(p3),1) < pixel_value_threshold:
                break
        if img[self._PhysToIndx(p3)] < pixel_value_threshold:
            p3 = p2
        dist = norm(p3-p2) + 0.5
        p4 = p3
        while img[self._PhysToIndx(p4)] > pixel_value_threshold:
            p3 = p4
            p4 = self._get_next_point(p2,p1,p2,dist)
            dist += 0.25
        return p3

    def _compute_trajectory(self,head_point,tail_point,distances,contact_len,contact_radius):
        """
        Computes the trajectory from tail_point -> head_point given a list of distances and the head and tail point\n
        Contact radius is unused

        ------------------------

        For every iteration it finds the next most probable center point of the cilinder between the one with the highest image momentum and the geometrical one\n
        the one with highest momentum is preferred if:
            - it's the first point
            - the geometric distance between the two is within 0.5 units of distance from the contacts distance\n

        Each vector is then multiplied by a correction vector that inverts the first two components

        """
        # first contact is the center of the cylinder with distance L/2 from the tip (tail)
        min_region_size = self.MIN_REGION_SIZE
        num_contacts = len(distances)
        min_cont_dist = self.CONTACTS_DIST-0.5; max_cont_dist = self.CONTACTS_DIST+0.5
        electrode = empty((num_contacts+1,len(tail_point)),dtype=float64)
        cylinder_center = tail_point
        distances = [-contact_len/2] + distances
        inverse_vect = array([ -1, -1, 1],dtype=float)

        for i in range(num_contacts+1):
            cylinder_center = self._get_next_point(cylinder_center,tail_point,head_point,contact_len + distances[i])
            cylinder_center_hm = self._get_point_with_highest_momentum(self._PhysToIndx(cylinder_center),min_region_size,min_region_size)
            electrode[i,:] = (cylinder_center_hm if cylinder_center_hm is not None and (i==0 or (min_cont_dist < norm(cylinder_center - cylinder_center_hm) < max_cont_dist)) else cylinder_center)*inverse_vect
        return electrode

    def _check_point(self,point):
        #TODO better checks
        return point is not None and point.shape[0] == 3

    def compute_electrode_trajectory(  self,
                                       start_end_points,
                                       contact_len = 2.0,
                                       contact_radius = 0.8,
                                       distances=None):
        '''
        Computes the trajectory from two points:
            - start_end_points : must be a dictionary of 
                [ ```h``` (head) XOR ```e``` (entry) ] AND [ ```t``` (target) XOR ```l``` (tail) ]
            - contact_len : float defining the length of each cylinder contact
            - contact_radius: float defining the cylinder radius of each contact
            - distances : a list of floats of distances between each contact
        '''
        h,e,t,l = [sym in set(start_end_points.keys()) for sym in ("h","e","t","l")]
        if not (((h and not e) or (not h and e)) and ((t and not l) or (not t and l))):
            raise Exception("Must provide either head or entry and either target or tail")
        #if not self._check_point(entry_point) or not self._check_point(target_point):
        #    raise Exception("Wrongly formatted points")

        head_point = self._find_head(start_end_points["e"]) if e else h
        if head_point is None:
            raise Exception('Cannot find head point')
        
        tail_point = self._find_tail(head_point,start_end_points["t"]) if t else l
        if tail_point is None:
            raise Exception('Cannot find tail point')
        
        return self._compute_trajectory(head_point,tail_point,distances,contact_len,contact_radius)

    

if __name__ == '__main__':
# command:
# ./deeto -ct /home/gagg/Desktop/deeto/DEETO/res/r_oarm_seeg_cleaned.nii.gz -e 61.8454 -19.8803 10.6827 -t 5.34427 -16.6807 8.2421 -m 18 2.0 0.8 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 1.5 
    sample_input = ({"e":array((61.8454, -19.8803, 10.6827)),
                    "t":array((5.34427, -16.6807, 8.2421))},
                    2.0, 
                    0.8, 
                    [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
                    
    deeto_obj = ElectrodeTrajectoryConstructor('res/ct.nii.gz')
   
    out_values = array([(-7.69635,16.6547,8.58488),
                   (-11.1888,16.8029,8.7768),
                   (-14.6808,16.9743,8.9406),
                   (-18.1727,17.1457,9.1044),
                   (-21.6647,17.3171,9.26819),
                   (-25.1566,17.4885,9.43199),
                   (-28.6486,17.6598,9.59578),
                   (-32.1406,17.8312,9.75958),
                   (-35.6325,18.0026,9.92338),
                   (-39.1245,18.174,10.0872),
                   (-42.6164,18.3454,10.251),
                   (-46.1084,18.5168,10.4148),
                   (-49.6004,18.6881,10.5786),
                   (-53.0923,18.8595,10.7424),
                   (-56.5843,19.0309,10.9062),
                   (-60.0763,19.2023,11.07),
                   (-63.5682,19.3737,11.2337),
                   (-67.0602,19.5451,11.3975)])
    trajectory_points = deeto_obj.compute_electrode_trajectory(*sample_input)
    norms = []
    for py_point_found,cpp_point_found in zip(trajectory_points,out_values):
        this_points_distance = norm(py_point_found-cpp_point_found)
        print("norm of cpp point and python point: "+str(this_points_distance))
        norms.append(this_points_distance)
    print("avg error: "+str(mean(norms)))