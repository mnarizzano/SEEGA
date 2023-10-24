from numpy import clip,subtract,array
from itertools import product

def is_valid_region(region,borders):
    '''
    gets a region as tuple of slices of N dimension and a tuple of start border and end border (both inclusive) of N dimension\n
    returns True if region is within borders\n
    soft checks on input are performed
    '''
    return borders is not None and region is not None and all(reg_slice.start >= min_val and reg_slice.stop <= max_val for reg_slice,(min_val,max_val) in zip(region,zip(borders[0],borders[1])))

def get_squared_region(center_point,region_size,clipping_min_max=None):
    '''
    creates a tuple of ndimensions of slices with start (center - region_size) and stop (center + region_size + 1) values that map a (possibly) squared region\n
    if clipping_min_max tuple is provided the region is clipped with borders (both inclusive)\n
    supports any dimension but does not check correctness of input
    '''
    if clipping_min_max is not None:
        min_v, max_v = clipping_min_max[0],clipping_min_max[1]
        start_point = clip(subtract(center_point,region_size),min_v,max_v)
        end_point = clip(subtract(center_point,-(region_size+1)),min_v,max_v)
    else:
        start_point = subtract(center_point,region_size)
        end_point = subtract(center_point,-(region_size+1))
    start_point = tuple(map(int,start_point))
    end_point = tuple(map(int,end_point))
    return tuple(slice(*start_end) for start_end in zip(start_point,end_point))    # returns slices

def get_region_size(region):
    '''
    returns a tuple of size for every dimension of the region given
    '''
    return tuple(reg_slice.stop-reg_slice.start for reg_slice in region)

def region_generator(center_point,region_size,clipping_min_max=None,C_style_iterator=False,as_np_array=False):
    '''
    Creates a squared region generator from a center and region_size half side.\n
    No checks on input correctness

    Params
    -------
        - center_point : the center as a tuple of points in whatever dimension (1D,2D,3D,4D,for more, a Sycamore chip is required)\n
        - region_size : size of the region (the square will be center - region to center + region with endpoint included)\n
        - C_style_iterator : if False loops from left to right, else from right to left
            example: in 2D and C_style_iterator False is for COLS { for ROWS { arr[ ROW , COL ] } }
    '''
    region = get_squared_region(center_point,region_size,clipping_min_max)
    if not C_style_iterator:
        for point in product(*(range(reg_slice.start, reg_slice.stop) for reg_slice in region[::-1])):
            if not as_np_array:
                yield tuple(reversed(point))
            else:
                yield array(tuple(reversed(point)),dtype=int)
    else:
        for point in product(*(range(reg_slice.start, reg_slice.stop) for reg_slice in region)):
            if not as_np_array:
                yield point
            else:
                yield array(point,dtype=int)