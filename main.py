import yaml
import os as sys
from io import StringIO
import numpy as numpy
from PIL import Image

class LZW__LVL1:

    def __init__(self, inletPath) -> None:
        self.codelength = 12
        self.inletName = sys.path.basename(inletPath).split(".")[0]
        self.inletExtension = sys.path.basename(inletPath).split(".")[1]
        if self.inletExtension == "txt":
            self.outputPath = sys.path.join(sys.path.dirname(inletPath), self.inletName + ".bin")
        elif self.inletExtension == "bin":
            self.outputPath = sys.path.join(sys.path.dirname(inletPath), "OutputText.txt")
        self.inletPath = inletPath

class LZW:
    def __init__(self, inletPath) -> None:
        self.inletName = sys.path.basename(inletPath).split(".")[0]
        self.inletExtension = "." + sys.path.basename(inletPath).split(".")[1]
        self.yamlPath = sys.path.join(sys.path.dirname(inletPath), self.inletName + ".yaml")
        if self.inletExtension in ["tiff",".png", ".bmp", ".jpg", ".jpeg", "txt"]:
            self.outputPath = sys.path.join(sys.path.dirname(inletPath), self.inletName + ".bin")
        elif self.inletExtension == ".bin":
            with open(self.yamlPath, "r") as yamlFile :
                yamlData = yaml.safe_load(yamlFile)
                extension = yamlData["extension"]
            self.outputPath = sys.path.join(sys.path.dirname(inletPath), "Output" + extension)
        self.inletPath = inletPath
        self.pivot = 0    # in case the job is level-3
        self.codelength = 32

class Level_1_Comp(LZW__LVL1):
    def __init__(self, inletPath):
        super().__init__(inletPath)
        self.listOfCompressed = []
        self.binaryString = ""
        self.byteArray = bytearray()
        self.compress()

    def DictionarySetter(self, data):
        dictionarySize = 256
        dictionary = {chr(i): i for i in range(dictionarySize)}
        w = ""
        for c in data:
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                self.listOfCompressed.append(dictionary[w])
                
                dictionary[wc] = dictionarySize
                dictionarySize += 1
                w = c
        if w:
            self.listOfCompressed.append(dictionary[w])

    def ETextPadder(self):
        extraPadding = 8 - len(self.binaryString) % 8
        for i in range(extraPadding):
            self.binaryString += "0"
        padded_info = "{0:08b}".format(extraPadding)
        self.binaryString = padded_info + self.binaryString

    def ByteArrayGetter(self):
        if (len(self.binaryString) % 8 != 0):
            print("Encoded text not padded properly")
            exit(0)

        for i in range(0, len(self.binaryString), 8):
            byte = self.binaryString[i:i + 8]
            self.byteArray.append(int(byte, 2))

    def IntArrToBS(self):
        bits = self.codelength
        for num in self.listOfCompressed:
            for n in range(bits):
                if num & (1 << (bits - 1 - n)):
                    self.binaryString += "1"
                else:
                    self.binaryString += "0"

    def compress(self):
        with open(self.inletPath, 'r+') as inletFile, open(self.outputPath, 'wb') as outputFile:
            data = inletFile.read()
            data = data.rstrip()
            self.DictionarySetter(data)
            self.IntArrToBS()
            self.ETextPadder()
            self.ByteArrayGetter()
            outputFile.write(bytes(self.byteArray))

class Level_1_Decomp(LZW__LVL1):
    def __init__(self, inletPath) -> None:
        super().__init__(inletPath)
        self.bitString = ""
        self.intCode = []
        self.decompressedText = None
        self.decompress()

    def GetDictionary(self):
        dictionarySize = 256
        dictionary = {i: chr(i) for i in range(dictionarySize)}
        result = StringIO()
        w = chr(self.intCode.pop(0))
        result.write(w)
        for k in self.intCode:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dictionarySize:
                entry = w + w[0]
            else:
                raise ValueError('Bad compressed k: %s' % k)
            result.write(entry)
            dictionary[dictionarySize] = w + entry[0]
            dictionarySize += 1
            w = entry
        self.decompressedText = result.getvalue()

    def PaddingRemover(self):
        padded_info = self.bitString[:8]
        extraPadding = int(padded_info, 2)
        self.bitString = self.bitString[8:]
        encodedText = self.bitString[:-1 * extraPadding]
        for bits in range(0, len(encodedText),self.codelength):
            self.intCode.append(int(encodedText[bits:bits+self.codelength],2))

    def decompress(self):
        with open(self.inletPath, 'rb') as inletFile, open(self.outputPath, 'w') as outputFile:
            byte = inletFile.read(1)
            while (len(byte) > 0):
                byte = ord(byte)
                bits = bin(byte)[2:].rjust(8, '0')
                self.bitString += bits
                byte = inletFile.read(1)
            self.PaddingRemover()
            self.GetDictionary()
            outputFile.write(self.decompressedText)

class Level_2_Comp(LZW):

    def __init__(self, inletPath):
        super().__init__(inletPath)
        self.image = None
        self.listOfCompressed = []
        self.binaryString = ""
        self.byteArray = bytearray()
        self.compress()

    def pilImageReader(self):
        self.image = Image.open(self.inletPath)
        self.image = self.image.convert('RGB')
    
    def flatImageConverter(self):
        img_gray = self.image.convert('L')
        img_array = numpy.array(img_gray)
        img_array = img_array.flatten().tolist()
        return img_array

    def dictionarySetter(self, data):
        dictionarySize = 256
        dictionary = {chr(i): i for i in range(dictionarySize)}
        w = ""
        for c in data:
            c = chr(c)
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                self.listOfCompressed.append(dictionary[w])
                dictionary[wc] = dictionarySize
                dictionarySize += 1
                w = c
        if w:
            self.listOfCompressed.append(dictionary[w])

    def textPadding(self):
        extraPadding = 8 - len(self.binaryString) % 8
        for i in range(extraPadding):
            self.binaryString += "0"
        padded_info = "{0:08b}".format(extraPadding)
        self.binaryString = padded_info + self.binaryString

    def byteArrayGetter(self):
        if (len(self.binaryString) % 8 != 0):
            print("Encoded text not padded properly")
            exit(0)
        for i in range(0, len(self.binaryString), 8):
            byte = self.binaryString[i:i + 8]
            self.byteArray.append(int(byte, 2))

    def arrayToBS(self):
        bits = self.codelength
        for num in self.listOfCompressed:
            for n in range(bits):
                if num & (1 << (bits - 1 - n)):
                    self.binaryString += "1"
                else:
                    self.binaryString += "0"

    def compress(self):
        with open(self.outputPath, 'wb') as outputFile, open(self.yamlPath, 'w') as yamlFile:
            self.pilImageReader()
            yaml.dump({"height": self.image.height, "width": self.image.width, "extension": self.inletExtension}, yamlFile)
            data = self.flatImageConverter()
            self.dictionarySetter(data)
            self.arrayToBS()
            self.textPadding()
            self.byteArrayGetter()            
            outputFile.write(bytes(self.byteArray))

class Level_2_Decomp(LZW):

    def __init__(self, inletPath) -> None:
        super().__init__(inletPath)
        self.bitString = ""
        self.intCode = []
        self.decompressed_image_array = []
        self.decompress()

    def npToPIL(self, width, height):
        arr = numpy.array(self.decompressed_image_array)
        arr = arr.reshape(height, width)
        img = Image.fromarray(numpy.uint8(arr))
        return img

    def GetDictionary(self):
        dictionarySize = 256
        dictionary = {i: chr(i) for i in range(dictionarySize)}
        result = StringIO()
        w = chr(self.intCode.pop(0))
        result.write(w)
        for k in self.intCode:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dictionarySize:
                entry = w + w[0]
            else:
                raise ValueError('Bad compressed k: %s' % k)
            result.write(entry)
            dictionary[dictionarySize] = w + entry[0]
            dictionarySize += 1
            w = entry
        self.decompressed_image_array = [ord(c) for c in result.getvalue()]

    def PaddingRemover(self):
        padded_info = self.bitString[:8]
        extraPadding = int(padded_info, 2)
        self.bitString = self.bitString[8:]
        encodedText = self.bitString[:-1 * extraPadding]
        for bits in range(0, len(encodedText),self.codelength):
            self.intCode.append(int(encodedText[bits:bits+self.codelength],2))

    def decompress(self):
        with open(self.inletPath, 'rb') as inletFile, open(self.yamlPath, 'r') as yamlFile:
            config_data = yaml.safe_load(yamlFile)
            width, height, extension = config_data["width"], config_data["height"], config_data["extension"]           
            byte = inletFile.read(1)
            while (len(byte) > 0):
                byte = ord(byte)
                bits = bin(byte)[2:].rjust(8, '0')
                self.bitString += bits
                byte = inletFile.read(1)               
            self.PaddingRemover()
            self.GetDictionary()
            image = self.npToPIL(width, height)
            outputPath__extended = sys.path.splitext(self.outputPath)[0] + extension
            image.save(self.outputPath)
            image.save(outputPath__extended)

class Level_3_Comp(LZW):

    def __init__(self, inletPath):
        super().__init__(inletPath)
        self.image = None
        self.listOfCompressed = []
        self.binaryString = ""
        self.byteArray = bytearray()
        self.compress()

    def FindDifference(self, arr):
        height, width = arr.shape
        newArray = numpy.array(arr, copy=True)
        for i in range(height):
            for j in range(1, width):
                newArray[i][j] = (int(arr[i][j])) - (int(arr[i][j - 1]))
        pivot = arr[0][0]
        newArray[0][0] = 0
        for i in range(1, height):
            newArray[i][0] = (int(arr[i][0])) - (int(arr[i - 1][0]))
        return newArray, pivot
    
    def PilImageReader(self):
        self.image = Image.open(self.inletPath)
        self.image = self.image.convert('RGB')

    def FlattenImage(self):
        img_gray = self.image.copy().convert('L')
        img_array = numpy.array(img_gray)
        img_array, grayPivot = self.FindDifference(img_array)
        self.pivot = int(grayPivot)
        img_array = img_array.flatten().tolist()
        return img_array

    def DictionarySetter(self, data):
        dictionarySize = 256
        dictionary = {chr(i): i for i in range(dictionarySize)}
        w = ""
        for c in data:
            c = chr(c)
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                self.listOfCompressed.append(dictionary[w])
                
                dictionary[wc] = dictionarySize
                dictionarySize += 1
                w = c
        if w:
            self.listOfCompressed.append(dictionary[w])

    def ETextPadder(self):
        extraPadding = 8 - len(self.binaryString) % 8
        for i in range(extraPadding):
            self.binaryString += "0"
        padded_info = "{0:08b}".format(extraPadding)
        self.binaryString = padded_info + self.binaryString

    def ByteArrayGetter(self):
        if (len(self.binaryString) % 8 != 0):
            print("Encoded text not padded properly")
            exit(0)
        for i in range(0, len(self.binaryString), 8):
            byte = self.binaryString[i:i + 8]
            self.byteArray.append(int(byte, 2))

    def IntArrToBS(self):
        bits = self.codelength
        for num in self.listOfCompressed:
            for n in range(bits):
                if num & (1 << (bits - 1 - n)):
                    self.binaryString += "1"
                else:
                    self.binaryString += "0"
                
    def compress(self):

        with open(self.outputPath, 'wb') as outputFile, open(self.yamlPath, 'w') as yamlFile:
            self.PilImageReader()
            data = self.FlattenImage()
            self.DictionarySetter(data)
            self.IntArrToBS()
            self.ETextPadder()
            self.ByteArrayGetter()
            yaml.dump({"height": self.image.height, "width": self.image.width, "extension": self.inletExtension, "pivot": self.pivot}, yamlFile)
            outputFile.write(bytes(self.byteArray))

class Level_3_Decomp(LZW):

    def __init__(self, inletPath) -> None:
        super().__init__(inletPath)
        self.bitString = ""
        self.intCode = []
        self.decompressed_image_array = []
        self.decompress()

    def DiffCalculator(self, arr, pivot):
        height, width = arr.shape
        newArray = numpy.array(arr, copy=True)
        newArray[0][0] = pivot
        for i in range(1, height):
            newArray[i][0] = (int(arr[i][0])) + (int(newArray[i - 1][0]))
        for i in range(1, width):
            for j in range(0, height):
                newArray[j][i] = (int(arr[j][i])) + (int(newArray[j][i - 1])) 
        return newArray

    def npToPIL(self, width, height, pivot):
        arr = numpy.array(self.decompressed_image_array)
        arr = arr.reshape(height, width)
        arr = self.DiffCalculator(arr, pivot)
        img = Image.fromarray(numpy.uint8(arr))
        return img

    def GetDictionary(self):
        dictionarySize = 256
        dictionary = {i: chr(i) for i in range(dictionarySize)}
        result = StringIO()
        w = chr(self.intCode.pop(0))
        result.write(w)
        for k in self.intCode:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dictionarySize:
                entry = w + w[0]
            else:
                raise ValueError('Bad compressed k: %s' % k)
            result.write(entry)
            dictionary[dictionarySize] = w + entry[0]
            dictionarySize += 1
            w = entry
        self.decompressed_image_array = [ord(c) for c in result.getvalue()]

    def PaddingRemover(self):
        padded_info = self.bitString[:8]
        extraPadding = int(padded_info, 2)
        self.bitString = self.bitString[8:]
        encodedText = self.bitString[:-1 * extraPadding]
        for bits in range(0, len(encodedText),self.codelength):
            self.intCode.append(int(encodedText[bits:bits+self.codelength],2))

    def decompress(self): 
        with open(self.inletPath, 'rb') as inletFile, open(self.yamlPath, 'r') as yamlFile:
            yamlData = yaml.safe_load(yamlFile)
            width, height, extension, pivot = yamlData["width"], yamlData["height"], yamlData["extension"], yamlData["pivot"]
            byte = inletFile.read(1)
            while (len(byte) > 0):
                byte = ord(byte)
                bits = bin(byte)[2:].rjust(8, '0')
                self.bitString += bits
                byte = inletFile.read(1)
            self.PaddingRemover()
            self.GetDictionary()
            image = self.npToPIL(width, height, pivot)
            image.save(self.outputPath)

class Level_4_Comp(LZW):

    def __init__(self, inletPath):
        super().__init__(inletPath)
        self.image = None
        self.listOfCompressed = []
        self.binaryString = ""
        self.byteArray = bytearray()
        self.compress()
    def PilImageReader(self):
        self.image = Image.open(self.inletPath)
        self.image = self.image.convert('RGB')
    
    def color_image_process(self):
        img_array = numpy.array(self.image)
        print(img_array.shape)
        biggest_shape_element = max(img_array.shape)
        if biggest_shape_element == img_array.shape[0]:
            img_array = numpy.pad(img_array, ((0,0), (0, biggest_shape_element - img_array.shape[1]), (0,0)), 'constant')
        elif biggest_shape_element == img_array.shape[1]:
            img_array = numpy.pad(img_array, ((0, biggest_shape_element - img_array.shape[0]), (0,0), (0,0)), 'constant')
        img_array = img_array.flatten().tolist()
        return img_array

    def DictionarySetter(self, data):
        dictionarySize = 256
        dictionary = {chr(i): i for i in range(dictionarySize)}
        w = ""
        for c in data:
            c = chr(c)
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                self.listOfCompressed.append(dictionary[w])
                dictionary[wc] = dictionarySize
                dictionarySize += 1
                w = c
        if w:
            self.listOfCompressed.append(dictionary[w])

    def ETextPadder(self):

        extraPadding = 8 - len(self.binaryString) % 8
        for i in range(extraPadding):
            self.binaryString += "0"
        padded_info = "{0:08b}".format(extraPadding)
        self.binaryString = padded_info + self.binaryString

    def ByteArrayGetter(self):
        if (len(self.binaryString) % 8 != 0):
            print("Encoded text not padded properly")
            exit(0)
        for i in range(0, len(self.binaryString), 8):
            byte = self.binaryString[i:i + 8]
            self.byteArray.append(int(byte, 2))

    def IntArrToBS(self):
        bits = self.codelength
        for num in self.listOfCompressed:
            for n in range(bits):
                if num & (1 << (bits - 1 - n)):
                    self.binaryString += "1"
                else:
                    self.binaryString += "0"

    def compress(self):

        with open(self.outputPath, 'wb') as outputFile, open(self.yamlPath, 'w') as yamlFile:
            self.PilImageReader()
            yaml.dump({"height": self.image.height, "width": self.image.width, "extension": self.inletExtension}, yamlFile)
            data = self.color_image_process()
            self.DictionarySetter(data)
            self.IntArrToBS()
            self.ETextPadder()
            self.ByteArrayGetter()
            outputFile.write(bytes(self.byteArray))

class Level_4_Decomp(LZW):

    def __init__(self, inletPath) -> None:
        super().__init__(inletPath)
        self.bitString = ""
        self.intCode = []
        self.decompressed_image_array = []
        self.decompress()

    def npToPIL(self, width, height):
        arr = numpy.array(self.decompressed_image_array)
        biggest_shape_element = max((width, height))
        arr = arr.reshape(biggest_shape_element, biggest_shape_element, 3)
        arr = arr[:height, :width, :]
        img = Image.fromarray(numpy.uint8(arr))
        return img

    def GetDictionary(self):
        dictionarySize = 256
        dictionary = {i: chr(i) for i in range(dictionarySize)}
        result = StringIO()
        w = chr(self.intCode.pop(0))
        result.write(w)
        for k in self.intCode:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dictionarySize:
                entry = w + w[0]
            else:
                raise ValueError('Bad compressed k: %s' % k)
            result.write(entry)
            dictionary[dictionarySize] = w + entry[0]
            dictionarySize += 1
            w = entry
        self.decompressed_image_array = [ord(c) for c in result.getvalue()]

    def PaddingRemover(self):
        padded_info = self.bitString[:8]
        extraPadding = int(padded_info, 2)
        self.bitString = self.bitString[8:]
        encodedText = self.bitString[:-1 * extraPadding]
        for bits in range(0, len(encodedText),self.codelength):
            self.intCode.append(int(encodedText[bits:bits+self.codelength],2))

    def decompress(self):
        with open(self.inletPath, 'rb') as inletFile, open(self.yamlPath, 'r') as yamlFile:
            yamlData = yaml.safe_load(yamlFile)
            width, height, extension = yamlData["width"], yamlData["height"], yamlData["extension"]
            byte = inletFile.read(1)
            while (len(byte) > 0):
                byte = ord(byte)
                bits = bin(byte)[2:].rjust(8, '0')
                self.bitString += bits
                byte = inletFile.read(1)
            self.PaddingRemover()
            self.GetDictionary()
            image = self.npToPIL(width, height)
            outputPath__extended = sys.path.splitext(self.outputPath)[0] + extension
            image.save(self.outputPath)
            image.save(outputPath__extended)

class Level_5_Comp(LZW):
    def __init__(self, inletPath):
        super().__init__(inletPath)
        self.image = None
        self.listOfCompressed = []
        self.binaryString = ""
        self.byteArray = bytearray()
        self.compress()

    def FindDifference(self, arr):
        height, width = arr.shape
        newArray = numpy.array(arr, copy=True)

        for i in range(height):
            for j in range(1, width):
                newArray[i][j] = (int(arr[i][j])) - (int(arr[i][j - 1]))
        
        pivot = arr[0][0]
        newArray[0][0] = 0
        for i in range(1, height):
            newArray[i][0] = (int(arr[i][0])) - (int(arr[i - 1][0]))

        return newArray, pivot
    
    def PilImageReader(self):
        self.image = Image.open(self.inletPath)
        self.image = self.image.convert('RGB')
    
    def color_image_process(self):
        img_array = numpy.array(self.image)
        rPivot = 0
        gPivot = 0
        bPivot = 0
        r = img_array[:, :, 0]
        g = img_array[:, :, 1]
        b = img_array[:, :, 2]

        r, rPivot = self.FindDifference(r)
        g, gPivot = self.FindDifference(g)
        b, bPivot = self.FindDifference(b)

        img_array = []
        for i in range(r.shape[0]):
            for j in range(r.shape[1]):
                img_array.append(r[i][j])
                img_array.append(g[i][j])
                img_array.append(b[i][j])

        return img_array, rPivot, gPivot, bPivot

    def DictionarySetter(self, data):
        dictionarySize = 256
        dictionary = {chr(i): i for i in range(dictionarySize)}
        w = ""
        for c in data:
            c = chr(c)
            wc = w + c
            if wc in dictionary:
                w = wc
            else:
                self.listOfCompressed.append(dictionary[w])
                
                dictionary[wc] = dictionarySize
                dictionarySize += 1
                w = c
        if w:
            self.listOfCompressed.append(dictionary[w])
    def ByteArrayGetter(self):
        if (len(self.binaryString) % 8 != 0):
            print("Encoded text not padded properly")
            exit(0)

        for i in range(0, len(self.binaryString), 8):
            byte = self.binaryString[i:i + 8]
            self.byteArray.append(int(byte, 2))

    def ETextPadder(self):
        extraPadding = 8 - len(self.binaryString) % 8
        for i in range(extraPadding):
            self.binaryString += "0"

        padded_info = "{0:08b}".format(extraPadding)
        self.binaryString = padded_info + self.binaryString



    def IntArrToBS(self):
        bits = self.codelength
        for num in self.listOfCompressed:
            for n in range(bits):
                if num & (1 << (bits - 1 - n)):
                    self.binaryString += "1"
                else:
                    self.binaryString += "0"

    def compress(self):

        with open(self.outputPath, 'wb') as outputFile, open(self.yamlPath, 'w') as yamlFile:
            
            self.PilImageReader()
            
            data, rPivot, gPivot, bPivot = self.color_image_process()

            self.DictionarySetter(data)
            self.IntArrToBS()
            self.ETextPadder()
            self.ByteArrayGetter()

            yaml.dump({"height": self.image.height, "width": self.image.width, "extension": self.inletExtension,
                       "rPivot": int(rPivot), "gPivot": int(gPivot), "bPivot": int(bPivot)}, yamlFile, indent=4)
            
            outputFile.write(bytes(self.byteArray))

class Level_5_Decomp(LZW):

    def __init__(self, inletPath) -> None:
        super().__init__(inletPath)

        self.bitString = ""
        self.intCode = []
        self.decompressed_image_array = []

        self.decompress()

    def DiffCalculator(self, arr, pivot):
        height, width = arr.shape
        newArray = numpy.array(arr, copy=True)
        newArray[0][0] = pivot

        for i in range(1, height):
            newArray[i][0] = (int(arr[i][0])) + (int(newArray[i - 1][0]))

        for i in range(1, width):
            for j in range(0, height):
                newArray[j][i] = (int(arr[j][i])) + (int(newArray[j][i - 1]))
    
        return newArray
    
    def npToPIL(self, width, height, rPivot, gPivot, bPivot):
        arr = numpy.array(self.decompressed_image_array)
        
        # 3D numpy array splitted 3 channel
        r = arr[0 : : 3].reshape(height, width)
        g = arr[1 : : 3].reshape(height, width)
        b = arr[2 : : 3].reshape(height, width)

        # Difference calculated for 3 channel
        r = self.DiffCalculator(r, rPivot)
        g = self.DiffCalculator(g, gPivot)
        b = self.DiffCalculator(b, bPivot)

        # R, G, B numpy arrays combined
        arr = numpy.zeros((height, width, 3), "uint8")
        arr[..., 0] = r
        arr[..., 1] = g
        arr[..., 2] = b

        img = Image.fromarray(numpy.uint8(arr))
        return img

    def GetDictionary(self):

        dictionarySize = 256
        dictionary = {i: chr(i) for i in range(dictionarySize)}

        result = StringIO()
        w = chr(self.intCode.pop(0))
        result.write(w)
        for k in self.intCode:
            if k in dictionary:
                entry = dictionary[k]
            elif k == dictionarySize:
                entry = w + w[0]
            else:
                raise ValueError('Bad compressed k: %s' % k)
            result.write(entry)

            dictionary[dictionarySize] = w + entry[0]
            dictionarySize += 1

            w = entry

        self.decompressed_image_array = [ord(c) for c in result.getvalue()]

    def PaddingRemover(self):

        padded_info = self.bitString[:8]
        extraPadding = int(padded_info, 2)
        self.bitString = self.bitString[8:]
        encodedText = self.bitString[:-1 * extraPadding]
        for bits in range(0, len(encodedText),self.codelength):
            self.intCode.append(int(encodedText[bits:bits+self.codelength],2))

    def decompress(self):
 
        with open(self.inletPath, 'rb') as inletFile, open(self.yamlPath, 'r') as yamlFile:

            yamlData = yaml.safe_load(yamlFile)
            width, height, extension = yamlData["width"], yamlData["height"], yamlData["extension"]
            rPivot, gPivot, bPivot = yamlData["rPivot"], yamlData["gPivot"], yamlData["bPivot"]
            
            byte = inletFile.read(1)
            while (len(byte) > 0):
                byte = ord(byte)
                bits = bin(byte)[2:].rjust(8, '0')
                self.bitString += bits
                byte = inletFile.read(1)
                
            self.PaddingRemover()

            self.GetDictionary()

            image = self.npToPIL(width, height, rPivot, gPivot, bPivot)

            outputPath__extended = sys.path.splitext(self.outputPath)[0] + extension
        
            image.save(self.outputPath)
            image.save(outputPath__extended)

class LZW:

    def __init__(self, inletPath, mode, level) -> None:

        if mode == "compression":
            if level == 1:
                Level_1_Comp(inletPath)
            elif level == 2:
                Level_2_Comp(inletPath)
            elif level == 3:
                Level_3_Comp(inletPath)
            elif level == 4:
                Level_4_Comp(inletPath)
            elif level == 5:
                Level_5_Comp(inletPath)
            else:
                raise ValueError("Wrong level")
        elif mode == "decompression":
            if level == 1:
                Level_1_Decomp(inletPath)
            elif level == 2:
                Level_2_Decomp(inletPath)
            elif level == 3:
                Level_3_Decomp(inletPath)
            elif level == 4:
                Level_4_Decomp(inletPath)
            elif level == 5:
                Level_5_Decomp(inletPath)
            else:
                raise ValueError("Wrong level")
        else:
            raise ValueError("Wrong mode")

LZW(r"testFiles\1\input.txt", "compression", 1)
LZW(r"testFiles\1\input.bin", "decompression", 1)
LZW(r"testFiles\2\input.png", "compression", 2)
LZW(r"testFiles\2\input.bin", "decompression", 2)
LZW(r"testFiles\3\input.png", "compression", 3)
LZW(r"testFiles\3\input.bin", "decompression", 3)
LZW(r"testFiles\4\input.png", "compression", 4)
LZW(r"testFiles\4\input.bin", "decompression", 4)
LZW(r"testFiles\5\input.png", "compression", 5)
LZW(r"testFiles\5\input.bin", "decompression", 5)