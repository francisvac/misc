from rosbag import Bag
new_bag_file = '2018-04-14-01-29-08_lidar_only.bag'
bag_file = '2018-04-14-01-29-08.bag'
old_topic_name = '/vlp16_1/velodyne_points'
new_topic_name = '/points_raw'
with Bag(new_bag_file, 'w') as Y:
    for topic, msg, t in Bag(bag_file):
    	if topic == old_topic_name:
    	    Y.write(new_topic_name,msg , t)