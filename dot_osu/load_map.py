__author__ = "Ehaschia"
import os
import re
from HintObjects import HitObjects, HintObjectsTable, NoneObject
from Timing import TimingTable
import Timing
import numpy as np
from slidertransfer import SliderTransfer

class load_osu:
    def __init__(self):
        pass

    GENETAL = ['AudioFilename', 'AudioLeadIn', 'PreviewTime', 'Countdown', 'SampleSet', 'StackLeniency', 'Mode',
               'LetterboxInBreaks', 'StoryFireInFront', 'EpilepsyWarning', 'CountdownOffset', 'WidescreenStoryboard']

    EDITOR = ['Bookmarks', 'DistanceSpacing', 'BeatDivisor', 'GridSize', 'TimelineZoom']

    METADATA = ['Title', 'TitleUnicode', 'Artist', 'ArtistUnicode', 'Creator', 'Version', 'Source', 'Tags', 'BeatmapID',
                'BeatmapSetID']

    DIFFICULTY = ['HPDrainRate', 'CircleSize', 'OverallDifficulty', 'ApproachRate', 'SliderMultiplier',
                  'SliderTickRate']

    def add_dic(self, name, dic, file_text, i):
        if file_text[i].find(name) != -1:
            dic[name] = file_text[i].split(':')[-1][:-1]

    def general_info(self, file_text, begin_row, end_row, dic):
        for i in range(begin_row, end_row):
            for j in self.GENETAL:
                self.add_dic(j, dic, file_text, i)

    def editor_info(self, file_text, begin_row, end_row, dic):
        for i in range(begin_row, end_row):
            for j in self.EDITOR:
                self.add_dic(j, dic, file_text, i)

    def metadata_info(self, file_text, begin_row, end_row, dic):
        for i in range(begin_row, end_row):
            for j in self.METADATA:
                self.add_dic(j, dic, file_text, i)

    def difficulty_info(self, file_text, begin_row, end_row, dic):
        for i in range(begin_row, end_row):
            for j in self.DIFFICULTY:
                self.add_dic(j, dic, file_text, i)

    def events_info(self, file_text, begin_row, end_row, dic):
        tmp_list = []
        flag = False
        for i in range(begin_row, end_row):
            if re.search('Break Periods', file_text[i]):
                for j in range(i + 1, end_row):
                    if file_text[j].find('//') != -1:
                        flag = True
                        break
                    else:
                        tmp_list.append(file_text[j])
            if flag:
                break

        if len(tmp_list) != 0:
            dic['Break Periods'] = tmp_list

    def timing_info(self, file_text, begin_row, end_row, dic):
        timing_table = TimingTable()

        for i in range(begin_row, end_row):
            timing_table.__add__(file_text[i])
        timing_table.music_seperate()
        dic['TimingPoints'] = timing_table

    def object_info(self, file_text, begin_row, end_row, dic):
        obj_table = HintObjectsTable()
        for i in range(begin_row, end_row):
            obj_table.add_object(file_text[i])
        dic['HitObjects'] = obj_table

    def text_to_dic(self, file_text):
        dic = {}
        row = 0
        line_cnt = len(file_text)
        # get the osu file format
        dic['format'] = int(re.search('\d+', file_text[row]).group(0))
        if dic['format'] < 10:
            return {}
        row += 1
        print "file format is v" + str(dic['format'])
        split_row = {}
        for row in range(1, line_cnt):
            if re.search('\[General\]', file_text[row]):
                split_row['General'] = row + 1
            if re.search('\[Editor\]', file_text[row]):
                split_row['Editor'] = row + 1
            if re.search('\[Metadata\]', file_text[row]):
                split_row['Metadata'] = row + 1
            if re.search('\[Difficulty\]', file_text[row]):
                split_row['Difficulty'] = row + 1
            if re.search('\[Events\]', file_text[row]):
                split_row['Events'] = row + 1
            if re.search('\[TimingPoints\]', file_text[row]):
                split_row['TimingPoints'] = row + 1
            if re.search('Colour', file_text[row]):
                split_row['Colours'] = row + 1
            if re.search('\[HitObjects\]', file_text[row]):
                split_row['HitObjects'] = row + 1
        split_row['End'] = line_cnt
        self.general_info(file_text, split_row['General'], split_row['Editor'] - 1, dic)
        if int(dic['Mode']) != 0:
            return {}
        self.editor_info(file_text, split_row['Editor'], split_row['Metadata'] - 1, dic)
        self.metadata_info(file_text, split_row['Metadata'], split_row['Difficulty'] - 1, dic)
        self.difficulty_info(file_text, split_row['Difficulty'], split_row['Events'] - 1, dic)
        self.events_info(file_text, split_row['Events'], split_row['TimingPoints'] - 1, dic)
        if split_row.has_key('Colours'):
            self.timing_info(file_text, split_row['TimingPoints'], split_row['Colours'] - 1, dic)
        else:
            self.timing_info(file_text, split_row['TimingPoints'], split_row['HitObjects'] - 1, dic)
        self.object_info(file_text, split_row['HitObjects'], split_row['End'], dic)
        return dic

    def osu_features(self, beatmap):
        res = []
        res.append(float(beatmap['HPDrainRate']))
        res.append(float(beatmap['CircleSize']))
        res.append(float(beatmap['OverallDifficulty']))
        res.append(float(beatmap['ApproachRate']))
        res.append(float(beatmap['SliderMultiplier']))
        # do we need this feature?
        res.append(float(beatmap['SliderTickRate']))
        return res

    def load_map(self, file_name):
        f = open(file_name, 'r')
        file_text = []
        try:
            for line in f:
                if len(line) <= 2:
                    if line != '\n':
                        print(line)
                    continue
                file_text.append(line)
        except Exception:
            raise ("read" + file_name + "fail.")
        finally:
            f.close()

        beatmap = self.text_to_dic(file_text)
        return beatmap

def generator_bmp_list(parsed_osu, tmp_sep):
    tmp_sep.append(parsed_osu['TimingPoints'].get_red_timing_list())
    tmp_sep.append( list(np.array(parsed_osu['TimingPoints'].get_mpb_list()) / int(parsed_osu['BeatDivisor'])))
    return tmp_sep

def get_finished_time(hit_object, timing):
    if hit_object.__class__ != 'Spinner':
        return hit_object.offset + timing.mpb
    else:
        tmp_transfer = SliderTransfer(hit_object)
        end_time = tmp_transfer.transfer(timing.get_speed())

def generator_music_info(beatmap_list):
    music_seperate_info = []
    for ii in beatmap_list:
        tmp_sep = [ii['SongFilePath']]
        tmp_sep = generator_bmp_list(ii, tmp_sep)
        music_seperate_info.append(tmp_sep)
    return music_seperate_info

def generator_objects_lists(parsed_osu):
    object = parsed_osu['HitObjects']
    # the use of test
    time_list = generator_bmp_list(parsed_osu, [])
    none = NoneObject()



if __name__ == '__main__':
    # find all map and songs
    file_dir = "E:/osu!/Songs/"
    map_list = []
    tmp_sep = []
    for root, dirs, files in os.walk(file_dir):
        for file in files:
            tmp_file = os.path.join(root, file)
            if re.search('\.osu', tmp_file):
                tmp_sep.append(tmp_file.split("\\")[0])
                map_list.append(tmp_file.replace('\\', '/'))
    # load a map
    beatmap_list = []
    map_paser = load_osu()
    for i in range(0, 2):
        tmp_parser = map_paser.load_map(map_list[i])
        if tmp_parser == {}:
            continue

        beatmap_list.append(tmp_parser)
        length = len(beatmap_list) - 1
        beatmap_list[length]["OsuFilePath"] = map_list[i]
        if beatmap_list[length]['AudioFilename'][0] == ' ':
            beatmap_list[length]['AudioFilename'] = beatmap_list[length]['AudioFilename'][1:]
        beatmap_list[length]["SongFilePath"] = tmp_sep[i] + "/" + beatmap_list[length]['AudioFilename']

    music_info = generator_music_info(beatmap_list)