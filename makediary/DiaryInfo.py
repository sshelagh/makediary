import sys
import getopt
import re
from os.path import join as path_join
from os.path import exists as path_exists
from glob import glob
from mx import DateTime
from ConfigParser import SafeConfigParser as ConfigParser
from os.path import expanduser
from math import pow

import PaperSize


class DiaryInfo:

    """ This class holds configuration information for the rest of the program, parses command
    line args, prints the usage message."""

    points_mm = 2.8346457               # Do all our work in millimetres

    sectionSep = "%-----------------\n" # Separator inside the postscript

    options = [
               "address-pages=",
               "appointments",
               "appointment-width=",
               "awk-ref",
               "colour",
               "colour-images",
               "conversions-ref",
               "cover-image=",
               "cover-page-image=",
               "day-title-shading=",
               "day-to-page",
               "debug-boxes",
               "debug-version",
               "debug-whole-page-boxes",
               "eps-page=",
               "eps-2page=",
               "event-images",
               "expense-pages=",
               "gridded-notes",
               "help",
               "image-page=",
               "image-2page=",
               "large-planner",
               "layout=",
               "line-spacing=",
               "man-page=",
               "margins-multiplier=",
               "moon",
               "northern-hemisphere-moon",
               "no-appointment-times",
               "no-smiley",
               "notes-pages=",
               "output-file=",
               "page-registration-marks",
               "page-size=",
               "page-x-offset=",
               "page-y-offset=",
               "paper-size=",
               "pcal",
               "pcal-planner",
               "pdf",
               "perpetual-calendars",
               "planner-years=",
               "ref=",
               "sed-ref",
               "sh-ref",
               "start-date=",
               "title=",
               "units-ref",
               "unix-ref",
               "vi-ref",
               "vim-ref",
               "week-to-opening",
               "weeks-before=",
               "weeks-after=",
               "version",
               "year=",
               ]

    usageStrings = \
                 [
                  "Usage: %s [--year=year | --start-date=yyyy-mm-dd]\n",
                  "    [--output-file=file] [--title=TITLE]\n",
                  "    [--address-pages=n] [--appointment-width=w] [--appointments]\n",
                  "    [--colour | --colour-images] [--cover-image=IMAGE]\n",
                  "    [--cover-page-image=IMAGE] [--day-to-page]\n",
                  "    [--day-title-shading=all|holidays|none]\n",
                  "    [--debug-boxes] [--debug-whole-page-boxes] [--debug-version]\n",
                  "    [--eps-page=epsfile[|title]] [--eps-2page=epsfile[|title1[|title2]]]\n",
                  "    [--event-images] [--expense-pages=0|2|4] [--gridded-notes]\n",
                  "    [--image-page=IMAGEFILE[,title]] [--image-2page=IMAGEFILE[,title]]\n",
                  "    [--large-planner] [--line-spacing=mm] [--margins-multiplier=f] [--moon]\n",
                  "    [--layout=LAYOUT] [--man-page=MANPAGE] [--northern-hemisphere-moon]\n",
                  "    [--no-appointment-times] [--no-smiley] [--notes-pages=n]\n",
                  "    [--page-registration-marks] [--page-x-offset=Xmm]\n",
                  "    [--page-y-offset=Ymm] [--pdf] [--planner-years=n] \n",
                  "    [--pcal] [--pcal-planner] [--perpetual-calendars]\n",
                  "    [--ref=<refname>] [--awk-ref] [--conversions-ref]\n",
                  "    [--sed-ref] [--sh-ref] [--units-ref] [--unix-ref] [--vi[m]-ref]\n",
                  "    [--weeks-before=n] [--weeks-after=n] [--week-to-opening]\n",
                  "    [--help] [--version]\n",
                  ]
    sizesString = "|".join(PaperSize.getPaperSizeNames())
    usageStrings.append("    [--page-size=%s]\n" % sizesString)
    usageStrings.append("    [--paper-size=%s]\n" % sizesString)
    usageStrings.append("  Defaults:\n")
    usageStrings.append("    year = next year          line-spacing = 6.0mm\n")
    usageStrings.append("    page-size = a5            paper-size = a5\n")
    usageStrings.append("    weeks-before = 0          weeks-after = 0\n")
    usageStrings.append("    appointment-width = 35%   planner-years = 2\n")
    usageStrings.append("    address-pages = 6         notes-pages = 6\n")

    layouts = ( "day-to-page", "week-to-opening", "week-to-2-openings", "work" )
    defaultLayout = "week-to-2-openings"
    usageStrings.append("  Layouts: " + ", ".join(layouts) + "\n")
    usageStrings.append("  Default layout: " + defaultLayout + "\n")

    def usage(self, f=sys.stderr):
        for i in range(len(self.usageStrings)):
            f.write(self.usageStrings[i])
        sys.exit(1)

    def shortUsage(self, f=sys.stderr):
        print >>f, "%s --help for usage" % self.myname
        sys.exit(1)

    def __init__(self, myname, opts):

        self.myname = myname
        self.opts = opts
        self.usageStrings[0] = self.usageStrings[0] % myname

        # first init the instance variables.
        self.pageNumber = 0             # Page number count
        self.currentJDaysLeft = -1      # Days left in year
        self.setStartDate(DateTime.DateTime(DateTime.now().year+1)) # Adjusted time, next year
        self.paperSize = 'a5'            # Page sizes.  Default to a5.
        wh = PaperSize.getPaperSize(self.paperSize)
        self.pageWidth = wh[0]
        self.pageHeight = wh[1]
        self.paperWidth = wh[0]
        self.paperHeight = wh[1]
        self.pageXOffset = 0.0
        self.pageYOffset = 0.0
        self.translatePage = 0
        self.translateXOffset = 0.0
        self.translateYOffset = 0.0
        self.iMargin = 12.0             # Page layout options
        self.oMargin = 5.0              #
        self.bMargin = 5.0              #
        self.tMargin = 5.0              #
        self.coverTitleFontSize = 20.0  #
        self.titleFontSize = 7.0        #
        self.titleFontName = "Times-Bold" #
        self.subtitleFontSize = 4.0     #
        self.subtitleFontName = "Helvetica" #
        self.personalinfoFontName = "Times-Bold" #
        self.personalinfoFixedFontName = "Courier-Bold" #
        self.titleY = -1                # Distance from bottom to title, calc from page size
        self.titleLineY = -1            #
        self.titleGray = 0.8            # Background for titles on some pages
        self.underlineThick = 0.2       # Thickness of title lines etc
        self.lineSpacing = 6.0          # Spacing for writing lines
        self.evenPage = 0               # even and odd pages
        self.out = None                 # Output file
        self.outName = 'diary.ps'       # Output file name
        self.outNameSet = False         # True if the output name set by command line opt.
        self.nAddressPages = 6          # Default
        self.nNotesPages = 6            #
        self.nPlannerYears = 2          #
        self.largePlanner = False       # Default: no large planner
        self.coverImage = None          # Pic for the cover page.
        self.coverPageImage = None      # Pic for the whole cover page.
        self.appointments = False       # Different "styles" for different people.
        self.appointmentTimes = True    # Print appointment times or not
        self.appointmentWidth = 35      # Width of appointments (as percentage)
        self.colour = False             # If true, print images in colour
        self.moon = False               # If true, print moon phases
        self.northernHemisphereMoon = False # If true, print northern hemisphere moon phases
        self.layout = self.defaultLayout
        self.debugBoxes = False         # If true, draw faint boxes around things for debugging
        self.debugVersion = False       # If true, print version info on inside cover.
        self.debugWholePageBoxes = False# If true, draw faint boxes around all pages.
        self.pageRegistrationMarks=False# Print marks to show where to cut.
        self.events = {}                # Events to draw on each page, from .calendar file.
        self.drawEventImages = False    # If true, draw event images
        self.nWeeksBefore = 0           # Print this number of weeks before the current year.
        self.nWeeksAfter = 0
        self.smiley = True
        self.imagePages = []
        self.manPages = []
        self.epsPages = []
        self.title = None
        self.pdf = False
        self.pcal = False
        self.pcalPlanner = False
        self.perpetualCalendars = False
        self.nExpensePages = 2
        self.griddedNotesPages = False
        self.dayTitleShading = "all"

        self.configOptions = ConfigParser()
        self.configOptions.read( (expanduser("~/.makediaryrc"), ".makediaryrc", "makediaryrc") )

        self.createMonthCalendars()

        self.parseOptions()
        self.readDotCalendar()


    def createMonthCalendars(self):
        '''Create all the month calendar names.

        There are only 14 possible yearly calendars - one for a year beginning on each day of
        the days of the week, and twice that for leap years.

        For each day of the week, we generate one set of month calendars that start on that day
        and finish on that day (ie 1JAN and 31DEC are the same day of the week) and another set
        where the year is an extra day longer.

        The idea is when something wants to print a month calendar, it can call in here with
        the year and month, and we will calculate exactly which calendar is to be printed, and
        return a name that will print that calendar in PostScript.
        '''
        self.monthCalendarList = {}
        for i in range(7):
            for m in range(1,13):
                self.monthCalendarList[ (m,i,i) ] = "M_m%02d_b%d_e%d" % (m,i,i)
                i2 = (i+1) % 7
                self.monthCalendarList[ (m,i,i2) ] = "M_m%02d_b%d_e%d" % (m,i,i2)

    def getMonthCalendarPsFnCall(self, year, month, addyear=True):
        '''Return the code to call a PostScript function that will print the appropriate
        calendar for a given year and month.

        If addYear==False, we return '() M_mMM_bB_eE', where MM is the month number, B is the
        day of week of the beginning of the year, and E is the day of week of the end of the
        year.

        If addYear is true, we return '(YYYY) M_mMM_bB_eE', where YYYY is the four digit year.
        '''
        dow_begin = DateTime.DateTime(year,  1,  1).day_of_week
        dow_end   = DateTime.DateTime(year, 12, 31).day_of_week
        k = (month, dow_begin, dow_end)
        if not self.monthCalendarList.has_key(k):
            print >>sys.stderr, "makediary: internal error:"
            print >>sys.stderr, "-- No month calendar for year=%s month=%s" % (str(year),str(month))
            sys.exit(1)
        procname = self.monthCalendarList[k]
        if addyear:
            return (" (%d) " % year) + procname
        else:
            return " () " + procname

    def parseOptions(self):
        args = self.opts
        # The first week day should be settable by command line option.
        #calendar.setfirstweekday(MONDAY)
        try:
            optlist,args = getopt.getopt(args,'',self.options)
        except getopt.error, reason:
            sys.stderr.write( "Error parsing options: " + str(reason) + "\n")
            self.shortUsage()
        if len(args) != 0:
            sys.stderr.write("Unknown arg: %s\n" % args[0] )
            self.shortUsage()
        for opt in optlist:
            if 0:  # Make it easier to move options around
                pass
            elif opt[0] == "--address-pages":
                self.nAddressPages = self.integerOption("address-pages",opt[1])
            elif opt[0] == "--appointment-width":
                self.appointments = True
                if opt[1][-1] == '%':
                    optstr = opt[1][0:-1] # Strip an optional trailing '%'
                else:
                    optstr = opt[1]
                self.appointmentWidth = self.floatOption("appointment-width",optstr)
                if self.appointmentWidth < 0 or self.appointmentWidth > 100:
                    sys.stderr.write("%s: appointment width must be >=0 and <=100\n" %
                                     self.myname)
                    sys.exit(1)
            elif opt[0] == "--appointments":
                self.appointments = True
            elif opt[0] == "--awk-ref":
                self.standardEPSRef( 'awk', ['Awk reference'] )
            elif opt[0] == "--colour" or opt[0] == "--colour-images":
                self.colour = True
            elif opt[0] == "--conversions-ref":
                self.standardEPSRef( 'conversions', ['Double conversion tables'] )
            elif opt[0] == "--cover-image":
                self.coverImage = opt[1]
            elif opt[0] == "--cover-page-image":
                self.coverPageImage = opt[1]
            elif opt[0] == "--day-title-shading":
                if opt[1] in ("all", "holidays", "none"):
                    self.dayTitleShading = opt[1]
                else:
                    print >>sys.stderr, "day-title-shading must be all or holiday or none" \
                        + " (not \"%s\")" % opt[1]
                    self.shortUsage();
            elif opt[0] == "--day-to-page":
                self.layout = "day-to-page"
            elif opt[0] == "--debug-boxes":
                self.debugBoxes = 1
            elif opt[0] == "--debug-whole-page-boxes":
                self.debugWholePageBoxes = 1
            elif opt[0] == "--debug-version":
                self.debugVersion = True
            elif opt[0] == "--eps-page":
                self.epsFilePageOption(opt[1], 1)
            elif opt[0] == "--eps-2page":
                self.epsFilePageOption(opt[1], 2)
            elif opt[0] == "--expense-pages":
                if opt[1] == '0' or opt[1] == '2' or opt[1] == '4':
                    self.nExpensePages = int(opt[1])
                else:
                    print >>sys.stderr, \
                          "%s: number of expense pages must be 0, 2, or 4 (not \"%s\")." % \
                          (sys.argv[0], opt[1])
                    self.shortUsage()
            elif opt[0] == "--perpetual-calendars":
                self.perpetualCalendars = True
            elif opt[0] == "--ref":
                name_and_titles = opt[1].split('|')
                self.standardEPSRef(name_and_titles[0], name_and_titles[1:])
            elif opt[0] == "--event-images":
                self.drawEventImages = True
            elif opt[0] == "--gridded-notes":
                self.griddedNotesPages = True
            elif opt[0] == "--help":
                self.usage(sys.stdout)
            elif opt[0] == "--image-page":
                self.imagePageOption(opt[1], 1)
            elif opt[0] == "--image-2page":
                self.imagePageOption(opt[1], 2)
            elif opt[0] == "--large-planner":
                self.largePlanner = True
            elif opt[0] == "--layout":
                if opt[1] in self.layouts:
                    self.layout = opt[1]
                else:
                    print >>sys.stderr, "%s: Unknown layout %s" % (self.myname, opt[1])
                    self.shortUsage()
            elif opt[0] == "--line-spacing":
                self.lineSpacing = self.floatOption("line-spacing",opt[1])
            elif opt[0] == "--man-page":
                self.manPageOption(opt[1])
            elif opt[0] == "--margins-multiplier":
                multiplier = self.floatOption("margins-multiplier",opt[1])
                self.tMargin = self.tMargin * multiplier
                self.bMargin = self.bMargin * multiplier
                self.iMargin = self.iMargin * multiplier
                self.oMargin = self.oMargin * multiplier
            elif opt[0] == "--moon":
                self.moon = True
            elif opt[0] == "--northern-hemisphere-moon":
                self.moon = True
                self.northernHemisphereMoon = True
            elif opt[0] == "--no-appointment-times":
                self.appointmentTimes = False
            elif opt[0] == "--no-smiley":
                self.smiley = False
            elif opt[0] == "--notes-pages":
                self.nNotesPages = self.integerOption("notes-pages",opt[1])
            elif opt[0] == '--output-file':
                self.outName = opt[1]
                self.outNameSet = True
            elif opt[0] == "--page-registration-marks":
                self.pageRegistrationMarks = True
            elif opt[0] == "--page-size":
                self.pageSize = opt[1]
                self.setPageSize(self.pageSize)
            elif opt[0] == "--page-x-offset":
                self.pageXOffset = self.floatOption("page-x-offset", opt[1])
            elif opt[0] == "--page-y-offset":
                self.pageYOffset = self.floatOption("page-y-offset", opt[1])
            elif opt[0] == "--pdf":
                self.pdf = True
            elif opt[0] == "--paper-size":
                self.paperSize = opt[1]
                self.setPaperSize(self.paperSize)
            elif opt[0] == "--pcal":
                self.pcal = True
            elif opt[0] == '--pcal-planner':
                self.pcal = True
                self.pcalPlanner = True
            elif opt[0] == "--planner-years":
                self.nPlannerYears = self.integerOption("planner-years",opt[1])
            elif opt[0] == "--version":
                print "makediary, version " + versionNumber
                sys.exit(0)
            elif opt[0] == "--sed-ref":
                self.standardEPSRef( 'sed', ['sed reference'] )
            elif opt[0] == "--sh-ref":
                self.standardEPSRef( 'sh', ['Shell and utility reference'] )
            elif opt[0] == '--start-date':
                self.setStartDate(DateTime.strptime(opt[1], '%Y-%m-%d'))
            elif opt[0] == "--title":
                self.title = opt[1]
            elif opt[0] == "--units-ref":
                self.standardEPSRef( 'units', ['Units'] )
            elif opt[0] == "--unix-ref":
                self.standardEPSRef( 'unix', ['Unix reference',] )
            elif opt[0] == "--vim-ref" or opt[0] == "--vi-ref":
                self.standardEPSRef( 'vi', ['Vi reference', 'Vim extensions'] )
            elif opt[0] == "--week-to-opening":
                self.layout = "week-to-opening"
            elif opt[0] == "--weeks-after":
                self.nWeeksAfter = self.integerOption("weeks-after",opt[1])
            elif opt[0] == "--weeks-before":
                self.nWeeksBefore = self.integerOption("weeks-before",opt[1])
            elif opt[0] == '--year':
                self.setStartDate(DateTime.DateTime(self.integerOption("year",opt[1])))
            else:
                print >>sys.stderr, "Unknown option: %s" % opt[0]
                self.shortUsage()
        if self.pdf:
            # If the name is still diary.ps and it was not set by command line option, change
            # it to diary.pdf.
            if (not self.outNameSet) and self.outName == 'diary.ps':
                self.outName = 'diary.pdf'
            # If we are doing PDF output, let ps2pdf open the output file.
            pdfArgs = ( 'ps2pdf',
                        '-dAutoRotatePages=/None', # pdf2ps rotates some pages without this
                        '-sPAPERSIZE='+self.paperSize,
                        '-', self.outName)
            #print >>sys.stderr, "Running "+str(pdfArgs)
            self.pdfProcess = subprocess.Popen(pdfArgs, stdin=subprocess.PIPE)
            self.out = self.pdfProcess.stdin
        else:
            if self.outName == '-':
                self.out = sys.stdout
            else:
                try:
                    self.out = open(self.outName,'w')
                except IOError, reason:
                    sys.stderr.write(("Error opening '%s': " % self.outName) \
                                     + str(reason) + "\n")
                    #self.usage()
                    sys.exit(1)
        self.calcPageLayout()
        self.calcDateStuff()


    def epsFilePageOption(self, option, npages):
        if npages == 1:
            options = option.split('|', 1)
            filename = options[0]
            if len(options) == 2:
                title1 = options[1]
            else:
                title1 = None
            title2 = None
        elif npages == 2:
            options = option.split('|', 2)
            filename = options[0]
            if len(options) >= 2:
                title1 = options[1]
            else:
                title1 = None
            if len(options) == 3:
                title2 = options[2]
            else:
                title2 = None
        else:
            print >>sys.stderr, "Strange number of pages for eps-page: %d" % npages
            return
        self.epsPages.append( {"fileName" : filename, "pages"  : npages,
                               "title1"   : title1,   "title2" : title2} )


    def standardEPSRef(self, name, titles):
        '''Find a list of files that make up a standard reference.'''
        # A weirdness: if we have only one title, use that for all pages.  But if we have more
        # than one title, use them in order until we run out.  So we have to know at the start
        # if we have one or more than one.
        same_title = (1 == len(titles))
        files = self.findEPSFiles(name)
        if len(files) == 0:
            print >>sys.stderr, "%s: cannot find ref files for \"%s\"" % \
                (sys.argv[0], name)
            return
        for f in files:
            if len(titles) > 0:
                title = titles[0]
                if not same_title:
                    titles = titles[1:]
            else:
                title = None
            self.epsPages.append( {"fileName" : f,     "pages"  : 1,
                                   "title1"   : title, "title2" : None } )


    def integerOption(self,name,s):
        """Convert an arg to an int."""
        try:
            return int(s)
        except ValueError,reason:
            sys.stderr.write("Error converting integer: " + str(reason) + "\n")
            self.shortUsage()


    def manPageOption(self, opt):
        match = re.match('''^([_a-z0-9][-_a-z0-9:\.]*)\(([1-9])\)$''', opt, re.IGNORECASE)
        if match:
            self.manPages.append( (match.group(1), match.group(2)) )
            return
        match = re.match('''^([_a-z0-9][-_a-z0-9:\.]*),([1-9])$''', opt, re.IGNORECASE)
        if match:
            self.manPages.append( (match.group(1), match.group(2)) )
            return

        match = re.match('''^([_a-z0-9][-_a-z0-9:\.]*)$''', opt, re.IGNORECASE)
        if match:
            self.manPages.append( (match.group(1), None) )
            return

        print >>sys.stderr, "%s: unknown man page: %s" % (sys.argv[0], opt)


    def setStartDate(self,date):
        self.dtbegin = DateTime.DateTime(date.year, date.month, date.day)
        self.dt = DateTime.DateTime(date.year, date.month, date.day)
        self.dtend = self.dt + DateTime.RelativeDateTime(years=1)


    def imagePageOption(self, option, npages):
        commaindex = option.find(",")
        if commaindex != -1:
            self.imagePages.append( { "fileName" : option[0:commaindex],
                                      "title"    : option[commaindex+1:],
                                      "pages"    : npages } )
        else:
            self.imagePages.append( { "fileName" : option,
                                      "title"    : "",
                                      "pages"    : npages } )


    def floatOption(self,name,s):
        """Convert an arg to a float."""
        try:
            return float(s)
        except ValueError,reason:
            sys.stderr.write("Error converting float: " + str(reason) + "\n")
            self.shortUsage()

    def setPageSize(self,s):
        """Set the page size to a known size."""
        sizes = PaperSize.getPaperSize(s)
        if sizes is None:
            print >>sys.stderr, "Unknown page size: %s" % s
            self.shortUsage()
        self.pageWidth = sizes[0]
        self.pageHeight = sizes[1]
        # Adjust font sizes with respect to A5, on a square root scale.
        self.adjustSizesForPageSize()

    def setPaperSize(self,s):
        """Set the paper size to a known size."""
        sizes = PaperSize.getPaperSize(s)
        if sizes is None:
            print >>sys.stderr, "Unknown paper size: %s" % s
            self.shortUsage()
        self.paperWidth = sizes[0]
        self.paperHeight = sizes[1]

    def adjustSizesForPageSize(self):

        """Change various sizes for a different sized page.

        The reference page size is A5.  Things are scaled up or down from there, but not
        linearly.  There are many magic numbers in here to make things ``just look right.''"""

        pageMultiple = self.pageHeight/210.0

        fontMultiplier = pow(pageMultiple, 0.9)
        self.titleFontSize *= fontMultiplier
        self.subtitleFontSize *= fontMultiplier

        coverTitleFontMultiplier = pageMultiple
        self.coverTitleFontSize *= coverTitleFontMultiplier

        marginMultiplier = pow(pageMultiple, 0.5)
        self.tMargin *= marginMultiplier
        self.bMargin *= marginMultiplier
        self.iMargin *= marginMultiplier
        self.oMargin *= marginMultiplier

    def calcPageLayout(self):

        # This should only be called once, just after the page size has been determined.
        # self.titleY leaves a smaller gap than the font size because the font does not
        # completely fill the box.

        # Calculate the offset.
        if self.pageWidth != self.paperWidth \
               or self.pageXOffset != 0 \
               or self.pageYOffset != 0:
            self.translateXOffset = ( self.paperWidth  - self.pageWidth  )/2.0 \
                                    + self.pageXOffset
            self.translateYOffset = ( self.paperHeight - self.pageHeight )/2.0 \
                                    + self.pageYOffset
            self.translatePage = 1

        self.titleY = self.bMargin \
                      + (self.pageHeight-(self.bMargin+self.tMargin)) \
                      - 0.8*self.titleFontSize
        self.titleLineY = self.titleY - self.titleFontSize*0.3

    def getNextPageNumber(self):
        # Each page calls this to get its page number.
        self.pageNumber = self.pageNumber + 1
        if (self.pageNumber % 2) == 0:
            self.evenPage=1
        else:
            self.evenPage=0
        return self.pageNumber

    def gotoNextDay(self):
        self.dt = self.dt + DateTime.oneDay
        self.calcDateStuff()

    def gotoPreviousDay(self):
        self.dt = self.dt - DateTime.oneDay
        self.calcDateStuff()

    def calcDateStuff(self):
        # Call this every time the day changes.
        if self.dt.is_leapyear:
            self.currentJDaysLeft = 366 - self.dt.day_of_year
        else:
            self.currentJDaysLeft = 365 - self.dt.day_of_year
        #sys.stderr.write("calcDateStuff: currentsec = %d\n" % self.currentSecond )


    def readDotCalendar(self):
        if self.pcal:
            import DotCalendarPcal as DotCalendar
        else:
            import DotCalendar
        dc = DotCalendar.DotCalendar()
        years = []
        for i in range(self.nPlannerYears+4):
            years.append(self.dtbegin.year-2+i)
        dc.setYears(years)
        dc.readCalendarFile()
        self.events = dc.datelist


    def findEPSFiles(self, name):
        '''Find EPS files matching a name.

        Given the "base name" of an EPS file, we search for files matching that, and return the
        path names in a list.

        For example, if we are given "sh", as the name to search for, and
        /usr/lib/site-python/makediary/eps/sh/sh.eps exists, we return that path in a sequence
        on its own.

        If given "sh", and /usr/.../sh.001.eps, sh.002.eps etc exist, we return all those in a
        sequence.

        We construct the names to search for by taking each element of the search path and
        appending /makediary/eps/<name>/<name>.eps and then /makediary/eps/<name>/<name>.*.eps
        to each element of the search path and checking to see if there are one or more files
        that match.  The first time we get a match we construct the list and return that.

        The search path is sys.path.  If makediary is being run with a relative path, then we
        first check a series of relative paths.

        If we are given a relative or absolute path to a file, use that only, after globbing.
        '''

        names = []
        # If we are given a full or relative-to-pwd path to the file, use that only.
        if '/' in name:
            names = glob(name)
        else:
            # Otherwise, construct the full path to the file.  If we are running from the
            # development directory, or otherwise not from a full path name, look at relative
            # locations first.  In any case, we search the current directory first.
            if sys.argv[0].startswith('.'):
                searchpaths = ['.', '..', '../..']
            else:
                searchpaths = ['.']
            for p in sys.path:
                searchpaths.append(p)
            #print >>sys.stderr, "searchpath is %s" % str(searchpath)
            for searchpath in searchpaths:
                path = path_join(searchpath, "makediary", "eps", "%s" % name, "%s.eps" % name)
                names = glob(path)
                if len(names) != 0:
                    break
                path = path_join(searchpath, "makediary", "eps", "%s" % name, "%s.*.eps" % name)
                names = glob(path)
                if len(names) != 0:
                    # glob() returns random or directory order, ie unsorted.
                    names.sort()
                    break
        return names

