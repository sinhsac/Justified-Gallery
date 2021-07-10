from JustifiedGallery import JustifiedGallery

test = JustifiedGallery('./photos', row_height=1024)
test.init_imgs()
test.start_img_analyzer(False)
test.collage.show()