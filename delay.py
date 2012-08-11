#!/usr/bin/python2
import pyaudio
import time
import wave 
from collections import deque
import gtk
import csv
import random

# Constants
chunk = 100 
p = pyaudio.PyAudio()

# Program
class DelayApp(gtk.Window):

  def __init__(self):
    super(DelayApp, self).__init__()
    self.set_title("Delay Experiment")
    
    # Necessary variables
    self.stopRecording = False
    
    # Buttons
    self.startExpBtn = gtk.Button("Start Experiment")
    self.startExpBtn.connect("clicked", self.startExp)
    self.stopRecBtn = gtk.Button("Stop Recording")
    self.stopRecBtn.connect("clicked", self.stopRec)
    self.startRecBtn = gtk.Button("Record New Stimulus")
    self.startRecBtn.connect("clicked", self.startRec)
    self.loadExpBtn = gtk.Button("Load Experiment")
    self.loadExpBtn.connect("clicked", self.loadExp)
    self.saveExpBtn = gtk.Button("Save Experiment")
    self.saveExpBtn.connect("clicked", self.saveExp)
    self.randBtn = gtk.Button("Randomize")
    self.randBtn.connect("clicked", self.randomize)

    # Text entry for new stimuli 
    self.filenameLabel = gtk.Label("Filename:")
    self.filename = gtk.Entry()

    # Text entry for new subject
    self.subjectNameLabel = gtk.Label("Subject Name:")
    self.subjectName = gtk.Entry()

    # Liststore for tests
    self.tests = gtk.ListStore(str, float)
    
    # Treeview for viewing and editing tests
    self.treeview = gtk.TreeView(self.tests)

    self.filecell = gtk.CellRendererText()
    self.filecell.set_property('editable', True)
    self.filecell.connect('edited', self.editedCB, 0)
    self.delaycell = gtk.CellRendererText()
    self.delaycell.set_property('editable', True)
    self.delaycell.connect('edited', self.editedCB, 1)
    self.filenameColumn = gtk.TreeViewColumn('Filename', self.filecell, text=0)
    self.delayColumn = gtk.TreeViewColumn('Delay', self.delaycell, text=1)
    self.treeview.append_column(self.filenameColumn)
    self.treeview.append_column(self.delayColumn)
    self.treeview.set_reorderable(True)
    
    # Layout
    self.hbox = gtk.HBox(spacing = 10)
    
    self.lvbox = gtk.VBox(spacing = 10)
    self.lvbox.pack_start(self.treeview)
    self.lvbox.pack_start(self.randBtn)
    
    self.rvbox = gtk.VBox(spacing = 10)
    
    self.rhbox_1 = gtk.HBox(spacing = 10)
    self.rhbox_1.pack_start(self.filenameLabel)
    self.rhbox_1.pack_start(self.filename)
    self.rhbox_1.pack_start(self.startRecBtn)
    
    self.rhbox_2 = gtk.HBox(spacing = 10)
    self.rhbox_2.pack_start(self.subjectNameLabel)
    self.rhbox_2.pack_start(self.subjectName)
    self.rhbox_2.pack_start(self.startExpBtn)

    self.rvbox.pack_start(self.rhbox_1)
    self.rvbox.pack_start(self.rhbox_2)
    self.rvbox.pack_start(self.stopRecBtn)
    self.rvbox.pack_start(self.saveExpBtn)
    self.rvbox.pack_start(self.loadExpBtn)

    self.hbox.pack_start(self.lvbox) 
    self.hbox.pack_start(self.rvbox)

    self.add(self.hbox)

    # GTK calls 
    self.connect("destroy", gtk.main_quit)
    self.set_position(gtk.WIN_POS_CENTER)
    self.show_all()
    gtk.main()
 
  def editedCB(self, cell, path, new_text, col):
    if col == 0:
      self.tests[path][col] = new_text
    else:
      self.tests[path][col] = float(new_text)

  def stopRec(self, widget):
    time.sleep(.5)
    self.stopRecording = True
  
  def startRec(self, widget):
    saveData(self.record(), "stimuli/" + self.filename.get_text())
    print "Added", [self.filename.get_text(), .180]
    self.tests.append([self.filename.get_text(), .180])
    print "Saved test: " + self.filename.get_text()

  def startExp(self, widget):
    outputs = set([])
    for i in range(len(self.tests)):
      (filename, delay) = self.tests[i]
      playFile("stimuli/" + filename)
      saveData(self.recordAndPlayWithDelay(delay), 
               "subjects/" + self.subjectName.get_text() + "-" + str(i + 1) + "-" + filename)
      outputs.add([self.subjectName.get_text(), i + 1, filename]) 
      print "Saved experiment results: " + \
            "subjects/" + self.subjectName.get_text() + "-" + str(i + 1) + "-" + filename

  def saveExp(self, widget):
    chooser = gtk.FileChooserDialog("Save...",
                                    None,
                                    gtk.FILE_CHOOSER_ACTION_SAVE,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    chooser.run()
    writer = csv.writer(open(chooser.get_filename(), 'wb'))
    for pair in self.tests:
      writer.writerow(pair)
    chooser.destroy()
    print "Saved experiment"
  
  def loadExp(self, widget):
    chooser = gtk.FileChooserDialog("Load...",
                                    None,
                                    gtk.FILE_CHOOSER_ACTION_OPEN,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    chooser.run()
    reader = csv.reader(open(chooser.get_filename(), 'r'))
    self.tests.clear()
    for row in reader: 
      if len(row) == 2:
        self.tests.append([row[0], float(row[1])])
#= [[row[0], float(row[1])] for row in reader if len(row) == 2] 

    chooser.destroy()
    print "Loaded experiment"

  def randomize(self, widget):
    x = range(len(self.tests)); random.shuffle(x);
    self.tests.reorder(x)

  def record(self):
    stream = p.open(format = pyaudio.paInt16,
                    channels = 1,
                    rate = 44100,
                    input = True,
                    frames_per_buffer = chunk)

    recording = []
    startTime = time.time()
    self.stopRecording = False 
    while self.stopRecording == False:
      data = stream.read(chunk)
      recording.append(data)
      gtk.main_iteration(block=False)

    stream.close()
    return ''.join(recording) 

  def recordAndPlayWithDelay(self, delay):
    stream = p.open(format = pyaudio.paInt16,
                    channels = 1,
                    rate = 44100,
                    input = True,
                    output = True,
                    frames_per_buffer = chunk)
    recording = []
    q = deque([])
    
    self.stopRecording = False
    while self.stopRecording == False:
      data = stream.read(chunk)
      q.append((time.time(), data))
      if time.time() - q[0][0] > delay:
        recording.append(q[0][1])
        stream.write(q.popleft()[1])
      gtk.main_iteration(block=False)

    stream.close()
    return ''.join(recording)


# Utilities
def playFile(filename):
  wf = wave.open(filename)
  stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                  channels = wf.getnchannels(),
                  rate = wf.getframerate(),
                  output = True)
  
  data = wf.readframes(chunk)
  while data != '':
    stream.write(data)
    data = wf.readframes(chunk)
  
  stream.close() 

def saveData(data, filename):
  wf = wave.open(filename, 'wb')
  wf.setnchannels(1)
  wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
  wf.setframerate(44100)
  wf.writeframes(data)
  wf.close()

# Main function
if __name__ == "__main__":
  app = DelayApp()
