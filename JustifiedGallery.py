import os.path
from PIL import Image, ImageEnhance
import math
import glob

class JustifiedGallery:
    def __init__(self, photo_path, width=4000, height=3000, row_height=300, margins=0, border=0, last_row='nojustify', justify_threshold=0.90):
        self.photo_path = photo_path
        self.count_imgs = 1
        self.width = width
        self.gallery_width = width
        self.height = height
        self.collage = Image.new("RGBA", (width, height))
        self.row_height = row_height
        self.margins = margins
        self.border = border
        self.last_analyzed_index = -1
        self.last_row = last_row
        self.max_rows_count = 0
        self.max_row_height = 1024
        self.justify_threshold = justify_threshold
        self.building_row = {
            "entries_buff": [],
            "width": 0,
            "height": 0,
            "aspect_ratio": 0
        }
        self._yield = {
            "every": 2, # do a flush every n flushes (must be greater than 1)
            "flushed": 0 # flushed rows without a yield
        }
        self.last_fetched_entry = None
        self.entries = []
        self.off_y = self.border
        self.rows = 0
        return

    def prepare_building_row(self, is_last_row, hidden_row):
        justify = True
        min_height = 0
        available_width = self.gallery_width - 2 * self.border - ((len(self.building_row['entries_buff']) - 1) * self.margins)
        row_height = available_width / self.building_row['aspect_ratio']
        default_row_height = self.row_height
        justifiable = False
        if self.building_row['width'] / available_width > self.justify_threshold:
            justifiable = True

        #With lastRow = nojustify, justify if is justificable(the images will not become too big)
        if is_last_row and not justifiable and self.last_row != 'justify' and self.last_row != 'hide':
            justify = False
            if self.rows > 0:
                default_row_height = (self.off_y - self.border - self.margins * self.rows) / self.rows;
                justify = default_row_height * self.building_row['aspect_ratio'] / available_width > self.justify_threshold;

        i = 0
        for entry in self.building_row['entries_buff']:
            img_aspect_ratio = entry['jg.width'] / entry['jg.height']

            new_img_w = default_row_height * img_aspect_ratio
            new_img_h = default_row_height
            if justify:
                if i == len(self.building_row['entries_buff']) - 1:
                    new_img_w = available_width
                else:
                    new_img_w = row_height * img_aspect_ratio
                    new_img_h = row_height
            available_width -= round(new_img_w)
            entry['jg.jwidth'] = round(new_img_w)
            entry['jg.jheight'] = math.ceil(new_img_h)
            entry['image'] = entry['image'].resize((round(new_img_w), math.ceil(new_img_h)))

            if i == 0 or min_height > new_img_h:
                min_height = new_img_h
            self.building_row['height'] = min_height
            i += 1
        return justify

    def analyze_images(self, is_for_resize):
        i = -1
        for entry in self.entries:
            i += 1
            if i < self.last_analyzed_index:
                continue
            available_width = self.gallery_width - 2 * self.border - ((len(self.building_row['entries_buff']) - 1) * self.margins)
            img_aspect_ratio = entry['jg.width'] / entry['jg.height']
            self.building_row['entries_buff'].append(entry)
            self.building_row['aspect_ratio'] += img_aspect_ratio
            self.building_row['width'] += img_aspect_ratio * self.row_height
            if available_width / (self.building_row['aspect_ratio'] + img_aspect_ratio) < self.row_height:
                self.flush_row(False, 0 < self.max_rows_count == self.rows)
                if self._yield['flushed'] >= self._yield['every']:
                    self._yield['flushed'] += 1
                    self.start_img_analyzer(is_for_resize)
                    self.last_analyzed_index = i
                    return
        self.last_analyzed_index = i

    def init_imgs(self):
        self.entries = []
        for filename in os.listdir(self.photo_path):
            path = os.path.join(self.photo_path, filename)
            im = Image.open(path)
            self.entries.append({
                "filename": filename,
                "path": path,
                "image": im,
                "jg.width": im.width,
                "jg.height": im.height
            })
        self.last_fetched_entry = self.entries[len(self.entries) - 1]

    def flush_row(self, is_last_row, hidden_row):
        building_row_res = self.prepare_building_row(is_last_row, hidden_row)
        off_x = self.border
        if hidden_row or (is_last_row and self.last_row == 'hide' and building_row_res):
            self.clear_building_row()
            return

        if self.max_row_height < self.building_row['height']:
            self.building_row['height'] = self.max_row_height

        if is_last_row and (self.last_row == 'center' or self.last_row == 'right'):
            available_width = self.gallery_width - 2 * self.border - (len(self.building_row['entries_buff']) - 1) * self.margins
            for entry in self.building_row['entries_buff']:
                available_width -= entry['jg.width']

            if self.last_row == 'center':
                off_x += round(available_width / 2)
            elif self.last_row == 'right':
                off_x += available_width

        for entry in self.building_row['entries_buff']:
            self.display_entry(entry, off_x, self.off_y, entry['jg.width'], entry['jg.height'], self.building_row['height'])
            off_x += entry['jg.jwidth'] + self.margins

        self.gallery_height_to_set = self.off_y + self.building_row['height'] + self.border

        if not is_last_row or (self.building_row['height'] <= self.row_height and building_row_res):
            self.off_y += self.building_row['height'] + self.margins
            self.rows += 1
            self.clear_building_row()
        pass

    def start_img_analyzer(self, is_for_resize):
        self.stop_img_analyzer_starter()
        self.analyze_images(is_for_resize)

    def clear_building_row(self):
        self.building_row['entries_buff'] = []
        self.building_row['aspect_ratio'] = 0
        self.building_row['width'] = 0
        pass

    def display_entry(self, img, off_x, off_y, img_width, img_height, row_height):
        print(img['filename'], off_x, off_y, img['image'].width, img['image'].height, row_height)
        self.collage.paste(img['image'], (off_x, int(off_y)))
        pass

    def stop_img_analyzer_starter(self):
        self._yield['flushed'] = 0

