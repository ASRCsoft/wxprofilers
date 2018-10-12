C-----------------------------------------------------------------------
C     This program was designed as a tool to assist users of the 
C     Radiosonde Replacement System's BUFR data to convert one or
C     more message types to text files.  
C
C     Credit goes to Jack Woollen of NCEP for the BUFR decoder
C     (bufr_1_xx.f) and a skeleton program for this program.
C
C     The flow of this program is to open and read the BUFR data
C     record by record.  Each record is tested to determine its 
C     message type.  Once the message type is determined, an array
C     for that message type gets initiated (a19 - a25).  Once the
C     appropriate array gets initialized, subroutines are called to
C     decode each variable and perform any necessary conversions.
C
C     NCDC provides this program "as is" with no warranties or 
C     guarantees as to its usefulness for any purpose.
C-----------------------------------------------------------------------
c
c    Revision 1.04
c     12/01/05/LJG -- Corrected error where release date in revision 
c        1.03 in Metadata sometimes got changed by routine that encodes 
c        O/P file date;  Values for missing were changed to whole numbers
c        for floating-point values.
c
c    Revision 1.03 
c     11/25/05/LJG -- Changed O/P path loop count to 0; added
c        detailed description option; added more descriptions
c        for filenames; revised output filename format;
c        Station name added to headings.
c        Output Filename:
c         pos 1 - 5  WBAN No,
c                 6  "_",
c             7 -16  YearMoDaHr  (Time of observation),
c                17  "_",
c            18 -26  "1Meta.txt" (7 message types)    
c                    "2rPTU.txt"
c                    "3GPSu.txt"
c                    "4GPSs.txt"
c                    "5pPTU.txt"
c                    "6pGPS.txt"
c                    "7Lvls.txt"
c
c    Revision 1.02
c     11/15/05/LJG -- Converted to accept program arguments from 
c        standard input rather than command line entries.  
c
c    Revision 1.01 
c     06/2005/LJG  Expanded code to decode all elements and write
c      text data to seven files.
c
      subroutine RRS_DECODER(bufrin, outpts)

      implicit none

      INTEGER MAXARR, IRET
      PARAMETER (MAXARR=100)

      CHARACTER*8 SUBSET
      REAL*8 ARR(MAXARR)
      REAL*8 a19(96), a20(36), a21(38), a22(38), a23(47), 
     &       a24(37), a25(33)
c
c    NCDC ADDED VARIABLES...
      character bufrin*80 
      character opt*1, rslash*1, tconv*1, outpts*7
c
      integer narg, iargc, idate, ireadsb, ireadmg, 
     & ix, lenout, ipos, ios
      logical gotbfr, doloop, dowrt(7)
c
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
c
C-----------------------------------------------------------------------
C-----------------------------------------------------------------------
c
c    SET FLAG TO OPEN FILES....
c
      op19 = .true.
      op20 = .true.
      op21 = .true.
      op22 = .true.
      op23 = .true.
      op24 = .true.
      op25 = .true.
c
      rslash = char(92)   ! Define Backslash or Reverse Slash...
c
c    NCDC ADDED CODE...
      write(6, 20) 
 20   format(/' Program: RRS_Decoder.exe   Ver. 1.04')
c
c   SET INPUT VARIABLES TO SPACES...
c
      do ix=1, 80
c$$$       bufrin(ix:ix) = ' '
       outdir(ix:ix) = ' '
      enddo
c
c  THE FOLLOWING COMMENTED OUT STATEMENTS ALLOW ENTRY OF PROGRAM 
c  ARGUMENT ON THE COMMAND LINE.  
c
c  THE FOLLOWING STATEMENTS WOULD ALLOW THE PROGRAM ARGUMENT(S)
c  TO BE ENTERED ON THE COMMAND LINE.  
c
c      narg = iargc()
c      if (narg .lt. 1 .or. narg .gt. 2) then
c        write(6,25)
c 25     format(/' ***ERROR:  RRS_Decoder:  incorrect usage'
c     &     /' Usage:  RRS_Decoder BUFR_Input_File  <O/P CODE>'
c     &    //' Press ENTER To EXIT Program')
c        read (5,'(a1)') opt
c        stop 
c      endif
c
c      call getarg(1,bufrin)
c
c      if (narg .eq. 1) then
c       outpts = '       '
c       call setwrt (outpts, dowrt)
c      else
c       call getarg(2, outpts)
c       call setwrt (outpts, dowrt)
c      endif        
c
c---------------------------------------------------
c
c  FOR DISTRIBUTION PURPOSES PROGRAM ARGUMENTS ARE ACCEPTED FROM 
c  STANDARD INPUT.  
c
c$$$      write(6, 30)
c$$$ 30   format(/' Enter BUFR Input Path and Filename:')
c$$$      read(5, '(a)') bufrin
c
c  LOCATE THE SEPARATING CHARACTER BETWEEN THE DIRECTORY AND
c  FILENAME.  THE DIRECTORY GETS USED IN THE CREATION OF 
c  OUTPUT FILENAMES.
c
      lendir = 80
      doloop = .true.
      do while (doloop .and. lendir .gt. 0)
       if (bufrin(lendir:lendir).eq.'/' .or. 
     &     bufrin(lendir:lendir).eq.rslash) then
        doloop = .false.
       else
        lendir = lendir - 1
       endif
      enddo
c
      outdir = bufrin(1:lendir)
c
c  DETERMINE WHETHER OR NOT THE BUFR FILE CAN BE FOUND.
c
      inquire(file=bufrin, exist=gotbfr)
      if (.not. gotbfr) then
        write(6, 55) bufrin 
 55     format(/' ***ERROR:  BUFR File NOT FOUND:'/a
     &    //' Press ENTER To EXIT Program')
        read (5,'(a1)') opt
        stop 
      endif
c
c   ACCEPT CODE INDICATING HOW TO HANDLE TEMPERATURES,
c   LEAVE AS KELVIN OR CONVERT TO CELCIUS.
c
      tconv = 'C'
c
c    CURRENTLY THE SOFTWARE DEFAULTS TO CELCIUS
c     write(6, 60)
c60   format(/' CHOOSE TEMPERATURE UNITS:  K = Kelvin,',
c    &   ' C = Celcius')
c     read(5, '(a1)') tconv
      call set_tc (tconv)
c
c$$$      outpts = '       '
c$$$c
c$$$      write(6, 70)
c$$$ 70   format(/'ENTER NUMERIC CODE FOR FILES TO WRITE: '
c$$$     & /'Example:  1234567 or a blank entry  Selects ALL'
c$$$     & /'          1257 selects metadata, and PTU Files'
c$$$     & /'  1 = Metadata,                 5 = processed PTU,'
c$$$     & /'  2 = raw PTU,                  6 = processed GPS,'
c$$$     & /'  3 = raw GPS unsmoothed,       7 = Standard & Sig Levels'
c$$$     & /'  4 = raw GPS smoothed,')
c$$$c
c$$$      read(5,'(a)') outpts
      call setwrt (outpts, dowrt)

C  OPEN THE FILE TO THE PROGRAM AND TO THE BUFRLIB
C  -----------------------------------------------

      OPEN( 8, FILE=bufrin, FORM='UNFORMATTED', STATUS='old',
     & ACCESS='sequential', IOSTAT=ios)
C
      write(6, 80)ios
 80   format(/'Opening BUFR file, IOSTAT =',i5)

      CALL OPENBF(8,'IN',8)
c
      fname = 'wbann_yearmodahr_0xxxx.txt'

c  READ THE RECORDS SEQUENTIALLY; PROCESS EACH TYPE IN KIND
c  --------------------------------------------------------

      DO WHILE(IREADMG(8,SUBSET,IDATE).EQ.0)
      DO WHILE(IREADSB(8).EQ.0)

      CALL UFBSEQ(8,ARR,MAXARR,1,IRET,SUBSET)

      IF(SUBSET.EQ.'NC002019') THEN

C assignment list for NC002019 002-019  9.4.1 RRS radiosonde complete registrat

       a19( 1) = arr(  1) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a19( 2) = arr(  2) ! CCITT IA  001062  SHORT ICAO LOCATION IDENTIFIER
       a19( 3) = arr(  3) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a19( 4) = arr(  4) ! CCITT IA  001062  SHORT ICAO LOCATION IDENTIFIER
       a19( 5) = arr(  5) ! NUMERIC   001001  WMO BLOCK NUMBER
       a19( 6) = arr(  6) ! NUMERIC   001002  WMO STATION NUMBER
       a19( 7) = arr(  7) ! NUMERIC   001094  WBAN NUMBER
       a19( 8) = arr(  8) ! CODE TAB  002011  RADIOSONDE TYPE
       a19( 9) = arr(  9) ! CCITT IA  001018  SHORT STATION OR SITE NAME (XXX
       a19(10) = arr( 10) ! CCITT IA  001095  RADIOSONDE OBSERVER
C       a19(11) = arr( 11) ! CCITT IA  025061  RRS WORKSTATION SOFTWARE VERSION
C       CALL READLC (8, SOFTV, 'SOFTV')
       a19(12) = arr( 12) ! NUMERIC   025068  RRS NUMBER OF ARCHIVE RECOMPUTES
       a19(13) = arr( 13) ! NUMERIC   001082  RRS RADIOSONDE ASCENSION NUMBER
       a19(14) = arr( 14) ! NUMERIC   001083  RRS RADIOSONDE RELEASE NUMBER
C       a19(15) = arr( 15) ! CCITT IA  001081  RRS RADIOSONDE SERIAL NUMBER
C       CALL READLC (8, RSERL, 'RSERL')
       a19(16) = arr( 16) ! HZ        002067  RRS RADIOSONDE OPERATING RADIO F
       a19(17) = arr( 17) ! CODE TAB  002066  RRS RADIOSONDE GROUND RECEIVING
       a19(18) = arr( 18) ! CODE TAB  002014  TRACKING TECHNIQUE/STATUS OF SYS
       a19(19) = arr( 19) ! PASCAL    025067  RRS RELEASE POINT PRESSURE CORRE
       a19(20) = arr( 20) ! DEGREE    025065  RRS ORIENTATION CORRECTION (AZIM
       a19(21) = arr( 21) ! DEGREE    025066  RRS ORIENTATION CORRECTION (ELEV
       a19(22) = arr( 22) ! CODE TAB  002095  RRS PRESSURE SENSOR TYPE CODE TA
       a19(23) = arr( 23) ! CODE TAB  002096  RRS TEMPERATURE SENSOR TYPE CODE
       a19(24) = arr( 24) ! CODE TAB  002097  RRS HUMIDITY SENSOR TYPE CODE TA
       a19(25) = arr( 25) ! FLAG TAB  002016  RRS RADIOSONDE CONFIGURATION
       a19(26) = arr( 26) ! CODE TAB  002083  RRS BALLOON SHELTER TYPE
       a19(27) = arr( 27) ! CODE TAB  002080  RRS BALLOON MANUFACTURER
       a19(28) = arr( 28) ! CODE TAB  002081  RRS BALLOON TYPE
C       a19(29) = arr( 29) ! CCITT IA  001093  RRS BALLOON LOT NUMBER
C       CALL READLC (8, BLOTN, 'BLOTN')
       a19(30) = arr( 30) ! CODE TAB  002084  RRS BALLOON GAS TYPE USED
       a19(31) = arr( 31) ! KG        002085  RRS BALLOON GAS AMOUNT USED
       a19(32) = arr( 32) ! METER     002086  RRS BALLOON FLIGHT TRAIN LENGTH
       a19(33) = arr( 33) ! KG        002082  RRS BALLOON WEIGHT
       a19(34) = arr( 34) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a19(35) = arr( 35) ! YEAR      004001  YEAR
       a19(36) = arr( 36) ! MONTH     004002  MONTH
       a19(37) = arr( 37) ! DAY       004003  DAY
       a19(38) = arr( 38) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a19(39) = arr( 39) ! YEAR      004001  YEAR
       a19(40) = arr( 40) ! MONTH     004002  MONTH
       a19(41) = arr( 41) ! DAY       004003  DAY
       a19(42) = arr( 42) ! HOUR      004004  HOUR
       a19(43) = arr( 43) ! MINUTE    004005  MINUTE
       a19(44) = arr( 44) ! SECOND    004006  SECOND
       a19(45) = arr( 45) ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a19(46) = arr( 46) ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a19(47) = arr( 47) ! METER     007001  STATION ELEVATION (BAROMETER LOC
       a19(48) = arr( 48) ! METER     007007  HEIGHT
       a19(49) = arr( 49) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a19(50) = arr( 50) ! CODE TAB  002115  RRS SURFACE WEATHER OBSERVING EQ
       a19(51) = arr( 51) ! PASCAL    010004  PRESSURE
       a19(52) = arr( 52) ! CODE TAB  002115  RRS SURFACE WEATHER OBSERVING EQ
       a19(53) = arr( 53) ! PERCENT   013003  RELATIVE HUMIDITY
       a19(54) = arr( 54) ! CODE TAB  002115  RRS SURFACE WEATHER OBSERVING EQ
       a19(55) = arr( 55) ! DEGREE T  011001  WIND DIRECTION
       a19(56) = arr( 56) ! METER/SE  011002  WIND SPEED
       a19(57) = arr( 57) ! CODE TAB  002115  RRS SURFACE WEATHER OBSERVING EQ
       a19(58) = arr( 58) ! DEGREE K  012101  TEMPERATURE/DRY BULB TEMPERATURE
       a19(59) = arr( 59) ! HOUR      004024  TIME PERIOD OR DISPLACEMENT (HOU
       a19(60) = arr( 60) ! DEGREE K  012101  TEMPERATURE/DRY BULB TEMPERATURE
       a19(61) = arr( 61) ! HOUR      004024  TIME PERIOD OR DISPLACEMENT (HOU
       a19(62) = arr( 62) ! CODE TAB  002115  RRS SURFACE WEATHER OBSERVING EQ
       a19(63) = arr( 63) ! DEGREE K  012103  DEW-POINT TEMPERATURE
       a19(64) = arr( 64) ! DEGREE K  012102  WET BULB TEMPERATURE
       a19(65) = arr( 65) ! CODE TAB  020012  CLOUD TYPE
       a19(66) = arr( 66) ! CODE TAB  020012  CLOUD TYPE
       a19(67) = arr( 67) ! CODE TAB  020012  CLOUD TYPE
       a19(68) = arr( 68) ! CODE TAB  020011  CLOUD AMOUNT
C      a19(69) = arr( 69) ! CODE TAB  020007  HEIGHT ABOVE SURFACE FOR BASE OF (OBSOLETE)
       a19(69) = arr( 69) ! CODE TAB  020011  HEIGHT OF BASE OF CLOUD         
       a19(70) = arr( 70) ! CODE TAB  020003  PRESENT WEATHER
       a19(71) = arr( 71) ! CODE TAB  020003  PRESENT WEATHER
       a19(72) = arr( 72) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a19(73) = arr( 73) ! DEGREE T  005021  BEARING OR AZIMUTH
       a19(74) = arr( 74) ! METER     007005  HEIGHT INCREMENT
       a19(75) = arr( 75) ! METERS    006021  DISTANCE
       a19(76) = arr( 76) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a19(77) = arr( 77) ! MINUTE    004025  TIME PERIOD OR DISPLACEMENT (MIN
       a19(78) = arr( 78) ! SECOND    004026  TIME PERIOD OR DISPLACEMENT (SEC
       a19(79) = arr( 79) ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a19(80) = arr( 80) ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a19(81) = arr( 81) ! YEAR      004001  YEAR
       a19(82) = arr( 82) ! MONTH     004002  MONTH
       a19(83) = arr( 83) ! DAY       004003  DAY
       a19(84) = arr( 84) ! HOUR      004004  HOUR
       a19(85) = arr( 85) ! MINUTE    004005  MINUTE
       a19(86) = arr( 86) ! SECOND    004006  SECOND
       a19(87) = arr( 87) ! FLAG TAB  025069  RRS FLIGHT LEVEL PRESSURE CORREC
       a19(88) = arr( 88) ! PASCAL    007004  PRESSURE
       a19(89) = arr( 89) ! PERCENT   013003  RELATIVE HUMIDITY
       a19(90) = arr( 90) ! CODE TAB  002013  SOLAR AND INFRARED RADIATION COR
       a19(91) = arr( 91) ! DEGREE K  012101  TEMPERATURE/DRY BULB TEMPERATURE
       a19(92) = arr( 92) ! METER     007009  GEOPOTENTIAL HEIGHT
C      a19(93) = arr( 93) ! CODE TAB  008077  TYPE OF RADIOSONDE TERMINATION (OBSOLETE)
C      a19(94) = arr( 94) ! CODE TAB  025022  REASON FOR TERMINATION (OBSOLETE)
C      a19(95) = arr( 95) ! CODE TAB  008077  TYPE OF RADIOSONDE TERMINATION (OBSOLETE)
C      a19(96) = arr( 96) ! CODE TAB  025022  REASON FOR TERMINATION (OBSOLETE)
       a19(93) = arr( 93) ! CODE TAB  008040  LVL SIGNIFICANCE FOR SOUNDING 
       a19(94) = arr( 94) ! CODE TAB  035035  REASON FOR TERMINATION
       a19(95) = arr( 95) ! CODE TAB  008040  LVL SIGNIFICANCE FOR SOUNDING 
       a19(96) = arr( 96) ! CODE TAB  035035  REASON FOR TERMINATION
c
       call unpk_19 (a19, tconv)
c
       if (dowrt(1)) then
        call writ_19
       endif

      ELSEIF(SUBSET.EQ.'NC002020') THEN

C assignment list for NC002020 002-020  9.4.2 RRS raw PTU

       a20( 1) = arr(  1) ! NUMERIC   001001  WMO BLOCK NUMBER
       a20( 2) = arr(  2) ! NUMERIC   001002  WMO STATION NUMBER
       a20( 3) = arr(  3) ! NUMERIC   001094  WBAN NUMBER
       a20( 4) = arr(  4) ! CODE TAB  002011  RADIOSONDE TYPE
       a20( 5) = arr(  5) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a20( 6) = arr(  6) ! YEAR      004001  YEAR
       a20( 7) = arr(  7) ! MONTH     004002  MONTH
       a20( 8) = arr(  8) ! DAY       004003  DAY
       a20( 9) = arr(  9) ! HOUR      004004  HOUR
       a20(10) = arr( 10) ! MINUTE    004005  MINUTE
       a20(11) = arr( 11) ! SECOND    004006  SECOND
       a20(12) = arr( 12) ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a20(13) = arr( 13) ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a20(14) = arr( 14) ! METER     007001  STATION ELEVATION (BAROMETER LOC
       a20(15) = arr( 15) ! METER     007007  HEIGHT
       a20(16) = arr( 16) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a20(17) = arr( 17) ! YEAR      004001  YEAR
       a20(18) = arr( 18) ! MONTH     004002  MONTH
       a20(19) = arr( 19) ! DAY       004003  DAY
       a20(20) = arr( 20) ! HOUR      004004  HOUR
       a20(21) = arr( 21) ! MINUTE    004005  MINUTE
       a20(22) = arr( 22) ! SECOND    004006  SECOND
       a20(23) = arr( 23) ! FLAG TAB  025069  RRS FLIGHT LEVEL PRESSURE CORREC
       a20(24) = arr( 24) ! PASCAL    007004  PRESSURE
       a20(25) = arr( 25) ! %         033007  DATA PERCENT CONFIDENCE (vendor-
       a20(26) = arr( 26) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a20(27) = arr( 27) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a20(28) = arr( 28) ! PERCENT   013009  RAW RELATIVE HUMIDITY
       a20(29) = arr( 29) ! %         033007  DATA PERCENT CONFIDENCE (vendor-
       a20(30) = arr( 30) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a20(31) = arr( 31) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a20(32) = arr( 32) ! CODE TAB  002013  SOLAR AND INFRARED RADIATION COR
       a20(33) = arr( 33) ! DEGREE K  012101  TEMPERATURE/DRY BULB TEMPERATURE
       a20(34) = arr( 34) ! %         033007  DATA PERCENT CONFIDENCE (vendor-
       a20(35) = arr( 35) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a20(36) = arr( 36) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
c
       if (dowrt(2)) then
        call unpk_20 (a20, tconv)
       endif

      ELSEIF(SUBSET.EQ.'NC002021') THEN

C assignment list for NC002021 002-021  9.4.3 RRS raw GPS unsmoothed

       a21( 1) = arr(  1) ! NUMERIC   001001  WMO BLOCK NUMBER
       a21( 2) = arr(  2) ! NUMERIC   001002  WMO STATION NUMBER
       a21( 3) = arr(  3) ! NUMERIC   001094  WBAN NUMBER
       a21( 4) = arr(  4) ! CODE TAB  002011  RADIOSONDE TYPE
       a21( 5) = arr(  5) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a21( 6) = arr(  6) ! YEAR      004001  YEAR
       a21( 7) = arr(  7) ! MONTH     004002  MONTH
       a21( 8) = arr(  8) ! DAY       004003  DAY
       a21( 9) = arr(  9) ! HOUR      004004  HOUR
       a21(10) = arr( 10) ! MINUTE    004005  MINUTE
       a21(11) = arr( 11) ! SECOND    004006  SECOND
       a21(12) = arr( 12) ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a21(13) = arr( 13) ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a21(14) = arr( 14) ! METER     007001  STATION ELEVATION (BAROMETER LOC
       a21(15) = arr( 15) ! METER     007007  HEIGHT
       a21(16) = arr( 16) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a21(17) = arr( 17) ! YEAR      004001  YEAR
       a21(18) = arr( 18) ! MONTH     004002  MONTH
       a21(19) = arr( 19) ! DAY       004003  DAY
       a21(20) = arr( 20) ! HOUR      004004  HOUR
       a21(21) = arr( 21) ! MINUTE    004005  MINUTE
       a21(22) = arr( 22) ! SECOND    004006  SECOND
       a21(23) = arr( 23) ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a21(24) = arr( 24) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a21(25) = arr( 25) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a21(26) = arr( 26) ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a21(27) = arr( 27) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a21(28) = arr( 28) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a21(29) = arr( 29) ! METER/SE  011003  U-COMPONENT
       a21(30) = arr( 30) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a21(31) = arr( 31) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a21(32) = arr( 32) ! METER/SE  011004  V-COMPONENT
       a21(33) = arr( 33) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a21(34) = arr( 34) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a21(35) = arr( 35) ! METER     007007  HEIGHT
       a21(36) = arr( 36) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a21(37) = arr( 37) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a21(38) = arr( 38) ! %         033007  DATA PERCENT CONFIDENCE (vendor-
c
       if (dowrt(3)) then
        call unpk_21 (a21)
       endif

       ELSEIF(SUBSET.EQ.'NC002022') THEN

C assignment list for NC002022 002-022  9.4.4 RRS raw GPS smoothed

       a22( 1) = arr(  1) ! NUMERIC   001001  WMO BLOCK NUMBER
       a22( 2) = arr(  2) ! NUMERIC   001002  WMO STATION NUMBER
       a22( 3) = arr(  3) ! NUMERIC   001094  WBAN NUMBER
       a22( 4) = arr(  4) ! CODE TAB  002011  RADIOSONDE TYPE
       a22( 5) = arr(  5) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a22( 6) = arr(  6) ! YEAR      004001  YEAR
       a22( 7) = arr(  7) ! MONTH     004002  MONTH
       a22( 8) = arr(  8) ! DAY       004003  DAY
       a22( 9) = arr(  9) ! HOUR      004004  HOUR
       a22(10) = arr( 10) ! MINUTE    004005  MINUTE
       a22(11) = arr( 11) ! SECOND    004006  SECOND
       a22(12) = arr( 12) ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a22(13) = arr( 13) ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a22(14) = arr( 14) ! METER     007001  STATION ELEVATION (BAROMETER LOC
       a22(15) = arr( 15) ! METER     007007  HEIGHT
       a22(16) = arr( 16) ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a22(17) = arr( 17) ! YEAR      004001  YEAR
       a22(18) = arr( 18) ! MONTH     004002  MONTH
       a22(19) = arr( 19) ! DAY       004003  DAY
       a22(20) = arr( 20) ! HOUR      004004  HOUR
       a22(21) = arr( 21) ! MINUTE    004005  MINUTE
       a22(22) = arr( 22) ! SECOND    004006  SECOND
       a22(23) = arr( 23) ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a22(24) = arr( 24) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a22(25) = arr( 25) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a22(26) = arr( 26) ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a22(27) = arr( 27) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a22(28) = arr( 28) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a22(29) = arr( 29) ! METER/SE  011003  U-COMPONENT
       a22(30) = arr( 30) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a22(31) = arr( 31) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a22(32) = arr( 32) ! METER/SE  011004  V-COMPONENT
       a22(33) = arr( 33) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a22(34) = arr( 34) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a22(35) = arr( 35) ! METER     007007  HEIGHT
       a22(36) = arr( 36) ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a22(37) = arr( 37) ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a22(38) = arr( 38) ! %         033007  DATA PERCENT CONFIDENCE (vendor-
c
       if (dowrt(4)) then
        call unpk_22 (a22)
       endif

       ELSEIF(SUBSET.EQ.'NC002023') THEN

C assignment list for NC002023 002-023  9.4.5 RRS processed PTU

       a23( 1) = arr(  1)  ! NUMERIC   001001  WMO BLOCK NUMBER
       a23( 2) = arr(  2)  ! NUMERIC   001002  WMO STATION NUMBER
       a23( 3) = arr(  3)  ! NUMERIC   001094  WBAN NUMBER
       a23( 4) = arr(  4)  ! CODE TAB  002011  RADIOSONDE TYPE
       a23( 5) = arr(  5)  ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a23( 6) = arr(  6)  ! YEAR      004001  YEAR
       a23( 7) = arr(  7)  ! MONTH     004002  MONTH
       a23( 8) = arr(  8)  ! DAY       004003  DAY
       a23( 9) = arr(  9)  ! HOUR      004004  HOUR
       a23(10) = arr( 10)  ! MINUTE    004005  MINUTE
       a23(11) = arr( 11)  ! SECOND    004006  SECOND
       a23(12) = arr( 12)  ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a23(13) = arr( 13)  ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a23(14) = arr( 14)  ! METER     007001  STATION ELEVATION (BAROMETER LOC
       a23(15) = arr( 15)  ! METER     007007  HEIGHT
       a23(16) = arr( 16)  ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a23(17) = arr( 17)  ! YEAR      004001  YEAR
       a23(18) = arr( 18)  ! MONTH     004002  MONTH
       a23(19) = arr( 19)  ! DAY       004003  DAY
       a23(20) = arr( 20)  ! HOUR      004004  HOUR
       a23(21) = arr( 21)  ! MINUTE    004005  MINUTE
       a23(22) = arr( 22)  ! SECOND    004006  SECOND
       a23(23) = arr( 23)  ! FLAG TAB  025069  RRS FLIGHT LEVEL PRESSURE CORREC
       a23(24) = arr( 24)  ! PASCAL    007004  PRESSURE
       a23(25) = arr( 25)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a23(26) = arr( 26)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a23(27) = arr( 27)  ! FLAG TAB  025069  RRS FLIGHT LEVEL PRESSURE CORREC
       a23(28) = arr( 28)  ! PASCAL    007004  PRESSURE
       a23(29) = arr( 29)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a23(30) = arr( 30)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a23(31) = arr( 31)  ! PERCENT   013003  RELATIVE HUMIDITY
       a23(32) = arr( 32)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a23(33) = arr( 33)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a23(34) = arr( 34)  ! CODE TAB  002013  SOLAR AND INFRARED RADIATION COR
       a23(35) = arr( 35)  ! DEGREE K  012101  TEMPERATURE/DRY BULB TEMPERATURE
       a23(36) = arr( 36)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a23(37) = arr( 37)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a23(38) = arr( 38)  ! CODE TAB  002013  SOLAR AND INFRARED RADIATION COR
       a23(39) = arr( 39)  ! DEGREE K  012101  TEMPERATURE/DRY BULB TEMPERATURE
       a23(40) = arr( 40)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a23(41) = arr( 41)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a23(42) = arr( 42)  ! DEGREE K  012103  DEW-POINT TEMPERATURE
       a23(43) = arr( 43)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a23(44) = arr( 44)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a23(45) = arr( 45)  ! METER     007009  GEOPOTENTIAL HEIGHT
       a23(46) = arr( 46)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a23(47) = arr( 47)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
c
       if (dowrt(5)) then
        call unpk_23(a23, tconv)
       endif

       ELSEIF(SUBSET.EQ.'NC002024') THEN

C assignment list for NC002024 002-024  9.4.6 RRS processed GPS

       a24( 1) = arr(  1)  ! NUMERIC   001001  WMO BLOCK NUMBER
       a24( 2) = arr(  2)  ! NUMERIC   001002  WMO STATION NUMBER
       a24( 3) = arr(  3)  ! NUMERIC   001094  WBAN NUMBER
       a24( 4) = arr(  4)  ! CODE TAB  002011  RADIOSONDE TYPE
       a24( 5) = arr(  5)  ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a24( 6) = arr(  6)  ! YEAR      004001  YEAR
       a24( 7) = arr(  7)  ! MONTH     004002  MONTH
       a24( 8) = arr(  8)  ! DAY       004003  DAY
       a24( 9) = arr(  9)  ! HOUR      004004  HOUR
       a24(10) = arr( 10)  ! MINUTE    004005  MINUTE
       a24(11) = arr( 11)  ! SECOND    004006  SECOND
       a24(12) = arr( 12)  ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a24(13) = arr( 13)  ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a24(14) = arr( 14)  ! METER     007001  STATION ELEVATION (BAROMETER LOC
       a24(15) = arr( 15)  ! METER     007007  HEIGHT
       a24(16) = arr( 16)  ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a24(17) = arr( 17)  ! YEAR      004001  YEAR
       a24(18) = arr( 18)  ! MONTH     004002  MONTH
       a24(19) = arr( 19)  ! DAY       004003  DAY
       a24(20) = arr( 20)  ! HOUR      004004  HOUR
       a24(21) = arr( 21)  ! MINUTE    004005  MINUTE
       a24(22) = arr( 22)  ! SECOND    004006  SECOND
       a24(23) = arr( 23)  ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a24(24) = arr( 24)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a24(25) = arr( 25)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a24(26) = arr( 26)  ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a24(27) = arr( 27)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a24(28) = arr( 28)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a24(29) = arr( 29)  ! METER/SE  011003  U-COMPONENT
       a24(30) = arr( 30)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a24(31) = arr( 31)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a24(32) = arr( 32)  ! METER/SE  011004  V-COMPONENT
       a24(33) = arr( 33)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a24(34) = arr( 34)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
       a24(35) = arr( 35)  ! METER     007007  HEIGHT
       a24(36) = arr( 36)  ! CODE TAB  033016  DATA QUALITY-MARK  INDICATOR (wo
       a24(37) = arr( 37)  ! CODE TAB  033015  DATA QUALITY-CHECK INDICATOR (wo
c
       if (dowrt(6)) then
        call unpk_24(a24)
       endif

       ELSEIF(SUBSET.EQ.'NC002025') THEN

C assignment list for NC002025 002-025  9.4.7 RRS standard and significant leve

       a25( 1) = arr(  1)  ! NUMERIC   001001  WMO BLOCK NUMBER
       a25( 2) = arr(  2)  ! NUMERIC   001002  WMO STATION NUMBER
       a25( 3) = arr(  3)  ! NUMERIC   001094  WBAN NUMBER
       a25( 4) = arr(  4)  ! CODE TAB  002011  RADIOSONDE TYPE
       a25( 5) = arr(  5)  ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a25( 6) = arr(  6)  ! YEAR      004001  YEAR
       a25( 7) = arr(  7)  ! MONTH     004002  MONTH
       a25( 8) = arr(  8)  ! DAY       004003  DAY
       a25( 9) = arr(  9)  ! HOUR      004004  HOUR
       a25(10) = arr( 10)  ! MINUTE    004005  MINUTE
       a25(11) = arr( 11)  ! SECOND    004006  SECOND
       a25(12) = arr( 12)  ! DEGREE    005001  LATITUDE (HIGH ACCURACY)
       a25(13) = arr( 13)  ! DEGREE    006001  LONGITUDE (HIGH ACCURACY)
       a25(14) = arr( 14)  ! METER     007001  STATION ELEVATION (BAROMETER LOC
       a25(15) = arr( 15)  ! METER     007007  HEIGHT
       a25(16) = arr( 16)  ! CODE TAB  008041  RRS DATA SIGNIFICANCE
       a25(17) = arr( 17)  ! YEAR      004001  YEAR
       a25(18) = arr( 18)  ! MONTH     004002  MONTH
       a25(19) = arr( 19)  ! DAY       004003  DAY
       a25(20) = arr( 20)  ! HOUR      004004  HOUR
       a25(21) = arr( 21)  ! MINUTE    004005  MINUTE
       a25(22) = arr( 22)  ! SECOND    004006  SECOND
       a25(23) = arr( 23)  ! CODE TAB  008040  LEVEL SIGNIFICANCE FOR RRS SOUND
       a25(24) = arr( 24)  ! FLAG TAB  025069  RRS FLIGHT LEVEL PRESSURE CORREC
       a25(25) = arr( 25)  ! PASCAL    007004  PRESSURE
       a25(26) = arr( 26)  ! PERCENT   013003  RELATIVE HUMIDITY
       a25(27) = arr( 27)  ! CODE TAB  002013  SOLAR AND INFRARED RADIATION COR
       a25(28) = arr( 28)  ! DEGREE K  012101  TEMPERATURE/DRY BULB TEMPERATURE
       a25(29) = arr( 29)  ! DEGREE K  012103  DEW-POINT TEMPERATURE
       a25(30) = arr( 30)  ! METER     007009  GEOPOTENTIAL HEIGHT
       a25(31) = arr( 31)  ! METER     007007  HEIGHT
       a25(32) = arr( 32)  ! METER/SE  011002  WIND SPEED
       a25(33) = arr( 33)  ! DEGREE T  011001  WIND DIRECTION
c
       if (dowrt(7)) then
        call unpk_25(a25, tconv)                                    
       endif

      ENDIF

C  END OF THE READ LOOPS
C  ---------------------

      ENDDO
      ENDDO
c
      close (19)
      close (20)
      close (21)
      close (22)
      close (23)
      close (24)
      close (25)
c
c$$$      write(6, 150)
c$$$ 150  format(/' Successful End, Press  ENTER  To EXIT')
c$$$      read(5, '(a1)') opt
c$$$      STOP 
      END
C
C========================================================
C
      SUBROUTINE set_tc (tconv)
       implicit none
c
       character*(*) tconv
c
       if (tconv .eq. 'k' .or. tconv .eq. 'K') then
        tconv = 'K'
       elseif (tconv .eq. 'c' .or. tconv .eq. 'C') then
        tconv = 'C'
       else
c
c  ASSIGN "C" IF UNMATCHED...
        tconv = 'C'      
       endif
       if (tconv.eq.'C') then
        write(6, 62) 
 62     format(/'NOTE:  Output Temperatures Are In CELCIUS')
       else
        write(6, 64)
 64     format(/'NOTE:  Output Temperatures Are In KELVIN')
       endif
c
       return
       end
C
C========================================================
C
      SUBROUTINE setwrt (outpts, dowrt)
c
      character*(*) outpts
      logical dowrt(7), doloop
      integer i
   
      do i=1, 7  ! initialize flags
       dowrt(i) = .false.
      enddo
c
      if (outpts .eq. '       ') then
       do i=1, 7
        dowrt(i) = .true.
       enddo
      else
       i = 0
       doloop = .true.
       do while (doloop .and. i.le.7)
        i = i + 1
        if (outpts(i:i).eq.' ') then
         doloop = .false.
        elseif (outpts(i:i).ge.'1'.and.outpts(i:i).le.'7') then
         read(outpts(i:i),'(i1)') ipos        
         dowrt(ipos) = .true.
        endif
       enddo
      endif
c
      return
      end
C
C========================================================
C
      SUBROUTINE unpk_19(a19, tconv)                                    
      implicit none
      REAL kelvin
      PARAMETER (kelvin=273.15)
c
      integer dsig1_19, dsig2_19, wmo19, wban19, ratp19, nrre, ascn,
     &     rrlse, rfreq, rgrsy, ttss, rrppc, psens, tsens, rhsens,
     &     rconf, bshel, bmfgr, btype, bgtyp, dsig3_19, b_yy, b_mo,
     &     b_dd, dsig4_19, r_yy19, r_mo19, r_dd19, r_hh19, rmin19,
     &     hbmsl19, heit19, dsig5_19, hinc, dsig6_19,
     &     sfeqp1, pr_19, sfeqp2, sfeqp3, wdir19, sfeqp4,
     &     tphr1, tphr2, sfeqp5, cltp1, cltp2, cltp3, clam, hocb, 
     &     prwe1, prwe2, dsig7_19, tpmi, t_yy, t_mo, t_dd, t_hh, tmin,
     &     flpc19, termpr, termsirc, termgph, termwsig, rtermwnd,
     &     termflt, rtermflt 
      real orcraz, orcrel, bgamt, bftln, bwght, rsec19, clat19, clon19,
     &     bearaz, dist, rh_19, wspd19, pasttd1, pasttd2, tdp19, tmwb,  
     &     tpse, clatterm, clonterm, tsec, termrh, term_td 
      character iclx1_19*4, iclx2_19*4, sstn19*5, obsvr19*4, SOFTV*12,
     &     RSERL*20, BLOTN*12

      common /admin/ dsig1_19, dsig2_19, wmo19, wban19, ratp19, nrre, 
     &  ascn, rrlse, rfreq, rgrsy, ttss, rrppc, psens, tsens, rhsens,
     &  rconf, bshel, bmfgr, btype, bgtyp, dsig3_19, b_yy, b_mo,
     &  b_dd, dsig4_19, r_yy19, r_mo19, r_dd19, r_hh19, rmin19,
     &  hbmsl19, heit19, dsig5_19, hinc, dist, dsig6_19,
     &  sfeqp1, pr_19, sfeqp2, sfeqp3, wdir19, sfeqp4,
     &  tphr1, tphr2, sfeqp5, cltp1, cltp2, cltp3, clam, hocb, 
     &  prwe1, prwe2, dsig7_19, tpmi, t_yy, t_mo, t_dd, t_hh, tmin,
     &  flpc19, termpr, termsirc, termgph, termwsig, rtermwnd,
     &  termflt, rtermflt,
     &  orcraz, orcrel, bgamt, bftln, bwght, rsec19, clat19, clon19,
     &  bearaz, rh_19, wspd19, pasttd1, pasttd2, tdp19, tmwb,  
     &  tpse, clatterm, clonterm, tsec, termrh, term_td, 
     &  iclx1_19, iclx2_19, sstn19, obsvr19, SOFTV,
     &  RSERL, BLOTN 
c
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
c
      CHARACTER*1 tconv
      CHARACTER*8  CVAL                                            
      EQUIVALENCE  (RVAL,CVAL)
      REAL*8       RVAL,BMISS
      REAL*8       a19(96)
c
      DATA BMISS /   10E10  /                                                
      
C---------------------------------------------------------------------- 
C---------------------------------------------------------------------- 
C
c  INITIALIZE FIELDS TO MISSING...
c
      dsig1_19 = -9
      iclx1_19 = 'MMMM'
      dsig2_19 = -9
      iclx2_19 = 'MMMM'
      wmo19 = 99999
      wban19 = 99999
      ratp19 = -9
      sstn19 = ' MMMM'
      obsvr19 = 'MMMM'
      SOFTV = '        MMMM'
      nrre = -9
      ascn = -9
      rrlse = -9
      RSERL = '                MMMM'
      rfreq = -9
      rgrsy = -9
      ttss = -9
      rrppc = 99999
      orcraz = -999.
      orcrel = -999.
      psens = -9
      tsens = -9
      rhsens = -9
      rconf = -9
      bshel = -9
      bmfgr = -9
      btype = -9
      BLOTN = '        MMMM'
      bgtyp = -9
      bgamt = -99.
      bftln = -99.
      bwght = -99.
      dsig3_19 = -9
      b_yy = 9999
      b_mo = 99
      b_dd = 99
      dsig4_19 = -9
      r_yy19 = 9999
      r_mo19 = 99
      r_dd19 = 99
      r_hh19 = 99
      rmin19 = 99
      rsec19 = 99.
      clat19 = -99.
      clon19 = -999.
      hbmsl19 = 99999
      heit19 = 99999
      dsig5_19 = -9
      bearaz = 999.
      hinc = 99999
      dist = 999.
      dsig6_19 = -9
      sfeqp1 = -9
      pr_19 = 999999
      sfeqp2 = -9
      rh_19 = -99. 
      sfeqp3 = -9
      wdir19 = 999
      wspd19 = 9999.
      sfeqp4 = -9
      pasttd1 = 999.
      tphr1 = 99
      pasttd2 = 999.
      tphr2 = 99
      sfeqp5 = -9
      tdp19 = 999.
      tmwb = 999.
      cltp1 = -9
      cltp2 = -9
      cltp3 = -9
      clam = -9
      hocb = -9999
      prwe1 = -9
      prwe2 = -9
      dsig7_19 = -9
      tpmi = -99
      tpse = 99.
      clatterm = -99.
      clonterm = -999.
      t_yy = 9999
      t_mo = 99
      t_dd = 99
      t_hh = 99
      tmin = 99
      tsec = 99.
      flpc19 = 999
      termpr = 999999
      termrh = -99.
      termsirc = -9
      term_td = 999. 
      termgph = 99999
      termwsig = -9
      rtermwnd = -9
      termflt = -9
      rtermflt = -9
c
      if (a19(1) .lt. bmiss) dsig1_19 = int(a19(1))
      rval = a19(2)
      iclx1_19 = cval(1:4)
      if (a19(3) .lt. bmiss) dsig2_19 = int(a19(3))
      rval = a19(4)
      iclx2_19 = cval(1:4)
c
c       WMO Block & Station No.
      if (a19(5) .lt. bmiss .and. a19(6) .lt. bmiss) then
       wmo19 = int(a19(5)*1000) + int(a19(6))
      endif
c
c       WBAN No.
      if (a19(7) .lt. bmiss) wban19 = int(a19(7))
c
      if (a19(8) .lt. bmiss) ratp19 = int(a19(8))
      rval = a19(9)
      sstn19 = cval(1:5)
      rval = a19(10)
      obsvr19 = cval(1:4)
      CALL READLC (8, SOFTV, 'SOFTV')
      if (a19(12) .lt. bmiss) nrre = int(a19(12))
      if (a19(13) .lt. bmiss) ascn = int(a19(13))
      if (a19(14) .lt. bmiss) rrlse = int(a19(14))
      CALL READLC (8, RSERL, 'RSERL')

      if (a19(16) .lt. bmiss) rfreq = int(a19(16))
      if (a19(17) .lt. bmiss) rgrsy = int(a19(17))
      if (a19(18) .lt. bmiss) ttss = int(a19(18))
      if (a19(19) .lt. bmiss) rrppc = int(a19(19))
      if (a19(20) .lt. bmiss) orcraz = a19(20)
      if (a19(21) .lt. bmiss) orcrel = a19(21)
      if (a19(22) .lt. bmiss) psens = int(a19(22))
      if (a19(23) .lt. bmiss) tsens = int(a19(23))
      if (a19(24) .lt. bmiss) rhsens = int(a19(24))
      if (a19(25) .lt. bmiss) rconf = int(a19(25))
      if (a19(26) .lt. bmiss) bshel = int(a19(26))
      if (a19(27) .lt. bmiss) bmfgr = int(a19(27))
      if (a19(28) .lt. bmiss) btype = int(a19(28))
      CALL READLC (8, BLOTN, 'BLOTN')
      if (a19(30) .lt. bmiss) bgtyp = int(a19(30))
      if (a19(31) .lt. bmiss) bgamt = a19(31)
      if (a19(32) .lt. bmiss) bftln = a19(32)
      if (a19(33) .lt. bmiss) bwght = a19(33)
      if (a19(34) .lt. bmiss) dsig3_19 = int(a19(34))
      if (a19(35) .lt. bmiss) b_yy = int(a19(35))
      if (a19(36) .lt. bmiss) b_mo = int(a19(36))
      if (a19(37) .lt. bmiss) b_dd = int(a19(37))
      if (a19(38) .lt. bmiss) dsig4_19 = int(a19(38))
      if (a19(39) .lt. bmiss) r_yy19 = int(a19(39))
      if (a19(40) .lt. bmiss) r_mo19 = int(a19(40))
      if (a19(41) .lt. bmiss) r_dd19 = int(a19(41))
      if (a19(42) .lt. bmiss) r_hh19 = int(a19(42))
      if (a19(43) .lt. bmiss) rmin19 = int(a19(43))
      if (a19(44) .lt. bmiss) rsec19 = a19(44)
      if (a19(45) .lt. bmiss) clat19 = a19(45)
      if (a19(46) .lt. bmiss) clon19 = a19(46)
      if (a19(47) .lt. bmiss) hbmsl19 = int(a19(47))
      if (a19(48) .lt. bmiss) heit19 = int(a19(48))
      if (a19(49) .lt. bmiss) dsig5_19 = int(a19(49))
      if (a19(50) .lt. bmiss) bearaz = a19(50)
      if (a19(51) .lt. bmiss) hinc = int(a19(51))
      if (a19(52) .lt. bmiss) dist = a19(52)
      if (a19(53) .lt. bmiss) dsig6_19 = int(a19(53))
      if (a19(54) .lt. bmiss) sfeqp1 = int(a19(54))
      if (a19(55) .lt. bmiss) pr_19 = int(a19(55))
      if (a19(56) .lt. bmiss) sfeqp2 = int(a19(56))
      if (a19(57) .lt. bmiss) rh_19 = a19(57)
      if (a19(58) .lt. bmiss) sfeqp3 = int(a19(58))
      if (a19(59) .lt. bmiss) wdir19 = int(a19(59))
      if (a19(60) .lt. bmiss) wspd19 = a19(60)
      if (a19(61) .lt. bmiss) sfeqp4 = int(a19(61))
      if (a19(62) .lt. bmiss) then
        if (tconv .eq. 'K') then
           pasttd1 = a19(62)
        else
           pasttd1 = a19(62) - kelvin
        endif
      endif
      if (a19(63) .lt. bmiss) tphr1 = int(a19(63))
      if (a19(64) .lt. bmiss) then
        if (tconv .eq. 'K') then
           pasttd2 = a19(64)
        else
           pasttd2 = a19(64) - kelvin
        endif
      endif
      if (a19(65) .lt. bmiss) tphr2 = int(a19(65))
      if (a19(66) .lt. bmiss) sfeqp5 = int(a19(66))
      if (a19(67) .lt. bmiss) then
        if (tconv .eq. 'K') then
           tdp19 = a19(67)
        else
           tdp19 = a19(67) - kelvin
        endif
      endif
      if (a19(68) .lt. bmiss) then
        if (tconv .eq. 'K') then
           tmwb = a19(68)
        else 
           tmwb = a19(68) - kelvin
        endif
      endif
      if (a19(69) .lt. bmiss) cltp1 = int(a19(69))
      if (a19(70) .lt. bmiss) cltp2 = int(a19(70))
      if (a19(71) .lt. bmiss) cltp3 = int(a19(71))
      if (a19(72) .lt. bmiss) clam = int(a19(72))
      if (a19(73) .lt. bmiss) hocb = int(a19(73))
      if (a19(74) .lt. bmiss) prwe1 = int(a19(74))
      if (a19(75) .lt. bmiss) prwe2 = int(a19(75))
      if (a19(76) .lt. bmiss) dsig7_19 = int(a19(76))
      if (a19(77) .lt. bmiss) tpmi = int(a19(77))
      if (a19(78) .lt. bmiss) tpse = a19(78)
      if (a19(79) .lt. bmiss) clatterm = a19(79)
      if (a19(80) .lt. bmiss) clonterm = a19(80)
      if (a19(81) .lt. bmiss) t_yy = int(a19(81))
      if (a19(82) .lt. bmiss) t_mo = int(a19(82))
      if (a19(83) .lt. bmiss) t_dd = int(a19(83))
      if (a19(84) .lt. bmiss) t_hh = int(a19(84))
      if (a19(85) .lt. bmiss) tmin = int(a19(85))
      if (a19(86) .lt. bmiss) tsec = a19(86)
      if (a19(87) .lt. bmiss) flpc19 = int(a19(87))
      if (a19(88) .lt. bmiss) termpr = int(a19(88))
      if (a19(89) .lt. bmiss) termrh = a19(89)
      if (a19(90) .lt. bmiss) termsirc = int(a19(90))
      if (a19(91) .lt. bmiss) then
        if (tconv .eq. 'K') then
           term_td = a19(91)
        else
           term_td = a19(91) - kelvin
        endif
      endif
      if (a19(92) .lt. bmiss) termgph = int(a19(92))
      if (a19(93) .lt. bmiss) termwsig = int(a19(93))
      if (a19(94) .lt. bmiss) rtermwnd = int(a19(94))
      if (a19(95) .lt. bmiss) termflt = int(a19(95))
      if (a19(96) .lt. bmiss) rtermflt = int(a19(96))
c
      call def_fname(wban19,r_yy19,r_mo19,r_dd19,r_hh19,rmin19)
      call getnam (wban19)
c
c   FOLLOWING CODE REPLACED BY writ_19 SUBROUTINE...
c
c     write(19, 100)
c100  format(/' DS CLX1 DS CLX2   WMO  WBAN RT  SStn Obs',
c    &  '  SoftV        NR Ascn R#')
c     write(19, 105)dsig1_19,iclx1_19,dsig2_19,iclx2_19,wmo19,
c    &  wban19,ratp19,sstn19,obsvr19,SOFTV,nrre,ascn,rrlse
c105  format(i3,1x,a4,i3,1x,a4,1x,i5.5,1x,i5.5,i3,1x,a5,1x,a4,
c    &  1x,a12,i3,i5,i3) 
c     write(19, 110)
c110  format(/' Serial #             Frequency GS TT RRPPC ORCRAZ',
c    &  ' ORCREL PS TS HS RC BS')
c     write(19, 115)RSERL,rfreq,rgrsy,ttss,rrppc,orcraz,orcrel,
c    &  psens,tsens,rhsens,rconf,bshel
c115  format(a20,i11,i3,i3,i6,2(f7.2),i3,i3,i3,i3,i3)
c     write(19, 120)
c120  format(/'BM BT Balloon_Lot# GT G_Amt TrLen BWght DS',
c    &  ' B_Yr Mo Da') 
c     write(19, 125)bmfgr,btype,BLOTN,bgtyp,bgamt,bftln,bwght,
c    &  dsig3_19,b_yy,b_mo,b_dd
c125  format(i2,i3,1x,a12,i3,f6.3,f6.1,f6.3,i3,1x,i4.4,2(1x,i2))
c     write(19, 130)
c130  format(/'DS R_Yr Mo Da Hr Mn   Sec      Lat        Lon ',
c    &  'Bar_Ht    Ht')
c     write(19, 135)dsig4_19,r_yy19,r_mo19,r_dd19,r_hh19,rmin19,
c    &  rsec19,clat19,clon19,hbmsl19,heit19
c135  format(i2,1x,i4.4,4(i3),f6.2,f10.5,f11.5,i6,i6)
c     write(19, 140)
c140  format(/'DS BearAz  HInc  Dist DS EQ  Press EQ    RH EQ',
c    &  '  WD   WSpd')
c     write(19, 145)dsig5_19,bearaz,hinc,dist,dsig6_19,sfeqp1,
c    &  pr_19,sfeqp2,rh_19,sfeqp3,wdir19,wspd19
c145  format(i2,f7.1,i6,f6.1,i3,i3,i7,i3,f6.1,i3,i4,f7.1)
c     write(19, 150)
c150  format(/'EQ  Td(k)  TP  Td(k)  TP EQ Tdp(k)  Tw(k) C1 C2 C3 CA',
c    &  '  HOCB PW PW')
c     write(19, 155)sfeqp4,pasttd1,tphr1,pasttd2,tphr2,sfeqp5,
c    &  tdp19,tmwb,cltp1,cltp2,cltp3,clam,hocb,prwe1,prwe2
c155  format(i2,f7.2,i4,f7.2,i4,i3,2f7.2,4i3,i6,2i3)
c     write(19, 160)
c160  format(
c    &  /'DS Tmi  Tsec  Term-Lat   Term-Lon T-Yr Mo Da Hr Mn   Sec')
c     write(19, 165)dsig7_19,tpmi,tpse,clatterm,clonterm,t_yy,t_mo,
c    & t_dd,t_hh,tmin,tsec
c165  format(i2,i4,f6.2,f10.5,f11.5,1x,i4.4,4i3,f6.2)
c     write(19, 170)
c170  format(/'FLPC TermPr  T_RH SR  T_Td T_GPH LS RT LS RT')
c     write(19, 175)flpc19,termpr,termrh,termsirc,term_td,
c    &  termgph,termwsig,rtermwnd,termflt,rtermflt
c175  format(i4,i7,f6.1,i3,f6.1,i6,4i3)
c
      return
      end
C
C========================================================
C

      SUBROUTINE def_fname(wban,i_yy,i_mm,i_dd,i_hh,i_min)
c
      implicit none
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
c
      integer wban,i_yy,i_mm,i_dd,i_hh,i_min
      integer iyy,imm,idd,ihh,imin
      integer da_mo(12), hm_lo(25), hm_hi(25), ob_hr(25), hrmn
      integer iobhr, ndx
c
      DATA da_mo/31,28,31,30,31,30,31,31,30,31,30,31/
c
c  hm_lo and hm_hi define the release time limits for assigning
c  the ob_hr value...
c
      data hm_lo/    0,   30,  130,  230,  330,  430,  530,  630,
     &  730,  830,  930, 1030, 1100, 1230, 1330, 1430, 1530, 1630,
     & 1730, 1830, 1930, 2030, 2130, 2230, 2300/
      data hm_hi/   29,  129,  229,  329,  429,  529,  629,  729,
     &  829,  929, 1029, 1059, 1229, 1329, 1429, 1529, 1629, 1729,
     & 1829, 1929, 2029, 2129, 2229, 2259, 2359/
      data ob_hr/   0,    1,     2,    3,    4,    5,    6,    7,
     &    8,    9,   10,   11,   12,   13,   14,   15,   16,   17,
     &   18,   19,   20,   21,   22,   23,    0/
c
c                 ASSIGN DATE INFO TO LOCAL VALUES
      iyy = i_yy
      imm = i_mm
      idd = i_dd
      ihh = i_hh
      imin = i_min
c
c     COMPUTE an Hour-Minute Value
      hrmn = (ihh * 100) + imin
      iobhr = -1
      ndx = 0
      do while (ndx .lt. 25 .and. iobhr .eq. -1)
       ndx = ndx + 1
       if (hrmn .ge. hm_lo(ndx) .and. hrmn .le. hm_hi(ndx)) then    
        iobhr = ob_hr(ndx)
       endif
      enddo
c
      if (iobhr .ne. -1) then
c
c    SHOULD DAY VALUE BE INCREASED BY 1 ???
       if (hrmn .ge. 2300 .and. hrmn .le. 2359) then
c           
c    ADD 1 TO DAY...
c    Before testing days/month, test for a 29 day February (Leap year)..
        if (mod(iyy,4) .eq. 0) then
         da_mo(2) = 29
        endif
        idd = idd + 1
        if (idd .gt. da_mo (imm)) then  !TEST DAYS
          idd = 1
          imm = imm + 1
          if (imm .gt. 12) then    ! TEST MONTH
           imm = 1
           iyy = iyy + 1
          endif
        endif
       endif
       write(fname(1:16), 30)wban,iyy,imm,idd,iobhr   
 30    format(i5.5,'_',i4.4,3(i2.2))
c
      else 
        write(6, *)'FAILED TO TRANSLATE TO AN OBSERVATION TIME FOR ',
     &   'THE OUTPUT FILENAMES'
        stop
      endif
c
      return
      end
C
C========================================================
C
      SUBROUTINE writ_19
      implicit none
c
      integer dsig1_19, dsig2_19, wmo19, wban19, ratp19, nrre, ascn,
     &     rrlse, rfreq, rgrsy, ttss, rrppc, psens, tsens, rhsens,
     &     rconf, bshel, bmfgr, btype, bgtyp, dsig3_19, b_yy, b_mo,
     &     b_dd, dsig4_19, r_yy19, r_mo19, r_dd19, r_hh19, rmin19,
     &     hbmsl19, heit19, dsig5_19, hinc, dsig6_19,
     &     sfeqp1, pr_19, sfeqp2, sfeqp3, wdir19, sfeqp4,
     &     tphr1, tphr2, sfeqp5, cltp1, cltp2, cltp3, clam, hocb, 
     &     prwe1, prwe2, dsig7_19, tpmi, t_yy, t_mo, t_dd, t_hh, tmin,
     &     flpc19, termpr, termsirc, termgph, termwsig, rtermwnd,
     &     termflt, rtermflt 
      real orcraz, orcrel, bgamt, bftln, bwght, rsec19, clat19, clon19,
     &     bearaz, dist, rh_19, wspd19, pasttd1, pasttd2, tdp19, tmwb,  
     &     tpse, clatterm, clonterm, tsec, termrh, term_td 
      character iclx1_19*4, iclx2_19*4, sstn19*5, obsvr19*4, SOFTV*12,
     &     RSERL*20, BLOTN*12

      common /admin/ dsig1_19, dsig2_19, wmo19, wban19, ratp19, nrre, 
     &  ascn, rrlse, rfreq, rgrsy, ttss, rrppc, psens, tsens, rhsens,
     &  rconf, bshel, bmfgr, btype, bgtyp, dsig3_19, b_yy, b_mo,
     &  b_dd, dsig4_19, r_yy19, r_mo19, r_dd19, r_hh19, rmin19,
     &  hbmsl19, heit19, dsig5_19, hinc, dist, dsig6_19,
     &  sfeqp1, pr_19, sfeqp2, sfeqp3, wdir19, sfeqp4,
     &  tphr1, tphr2, sfeqp5, cltp1, cltp2, cltp3, clam, hocb, 
     &  prwe1, prwe2, dsig7_19, tpmi, t_yy, t_mo, t_dd, t_hh, tmin,
     &  flpc19, termpr, termsirc, termgph, termwsig, rtermwnd,
     &  termflt, rtermflt,
     &  orcraz, orcrel, bgamt, bftln, bwght, rsec19, clat19, clon19,
     &  bearaz, rh_19, wspd19, pasttd1, pasttd2, tdp19, tmwb,  
     &  tpse, clatterm, clonterm, tsec, termrh, term_td, 
     &  iclx1_19, iclx2_19, sstn19, obsvr19, SOFTV,
     &  RSERL, BLOTN 
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
C
      character*100 of19
      character*60 desc(96)
      integer iret, lenout
                                                                        
      data desc /
     &'DATA SIGNIFICANCE,  Code Table 9-21  parent/WFO site',
     &'SHORT ICAO LOCATION IDENTIFIER',
     &'DATA SIGNIFICANCE,  Code Table 9-21  RRS obs site',
     &'SHORT ICAO LOCATION IDENTIFIER',
     &' ',
     &'WMO BLOCK AND STATION NUMBER',
     &'WBAN NUMBER',
     &'RADIOSONDE TYPE,  Code Table 9-1',
     &'SHORT STATION OR SITE NAME',
     &'RADIOSONDE OBSERVER',
     &'WORKSTATION SOFTWARE VERSION NUMBER',
     &'NUMBER OF ARCHIVE RECOMPUTES',
     &'RADIOSONDE ASCENSION NUMBER',
     &'RADIOSONDE RELEASE NUMBER', 
     &'RADIOSONDE SERIAL NUMBER', 
     &'RADIOSONDE OPERATING RADIO FREQUENCY',
     &'RADIOSONDE GROUND RECEIVING SYSTEM,  Code Table 9-5',
     &'TRACKING TECHNIQUE/STATUS OF SYSTEM,  Code Table 9-6',
     &'RELEASE POINT PRESSURE CORRECTION',
     &'ORIENTATION CORRECTION (AZIMUTH)',
     &'ORIENTATION CORRECTION (ELEVATION)',
     &'PRESSURE SENSOR TYPE,  Code Table 9-2',
     &'TEMPERATURE SENSOR TYPE,  Code Table 9-3',
     &'HUMIDITY SENSOR TYPE,  Code Table 9-4',
     &'RADIOSONDE CONFIGURATION,  Code Table 9-10c',
     &'BALLOON SHELTER TYPE,  Code Table 9-8',
     &'BALLOON MANUFACTURER,  Code Table 9-9',
     &'BALLOON TYPE, Code Table 9-10a',
     &'BALLOON LOT NUMBER',
     &'BALLOON GAS TYPE USED,  Code Table 9-10b',
     &'BALLOON GAS AMOUNT USED',
     &'BALLOON FLIGHT TRAIN LENGTH',
     &'BALLOON WEIGHT',
     &'DATA SIGNIFICANCE,  Code Table 9-21  Balloon mfg. date',
     &'YEAR',
     &'MONTH',
     &'DAY',
     &'DATA SIGNIFICANCE,  Code Table 9-21, balloon launch point',
     &'YEAR',
     &'MONTH',
     &'DAY',
     &'HOUR',
     &'MINUTE',
     &'SECOND',
     &'LATITUDE (HIGH ACCURACY)',
     &'LONGITUDE (HIGH ACCURACY)',
     &'HEIGHT OF BAROMETER ABOVE MSL',
     &'HEIGHT',
     &'DATA SIGNIFICANCE,  Code Table 9-21, sfc obs displacement',
     &'BEARING OR AZIMUTH',
     &'HEIGHT INCREMENT',
     &'DISTANCE',
     &'DATA SIGNIFICANCE,  Code Table 9-21, surface obs',
     &'SURFACE WEATHER OBSERVING EQUIPMENT USED,  Code Table 9-7',
     &'PRESSURE',
     &'SURFACE WEATHER OBSERVING EQUIPMENT USED,  Code Table 9-7',
     &'RELATIVE HUMIDITY',
     &'SURFACE WEATHER OBSERVING EQUIPMENT USED,  Code Table 9-7',
     &'WIND DIRECTION',
     &'WIND SPEED',
     &'SURFACE WEATHER OBSERVING EQUIPMENT USED,  Code Table 9-7',
     &'TEMPERATURE/DRY BULB TEMPERATURE',
     &'TIME PERIOD OR DISPLACEMENT (HOUR)',
     &'TEMPERATURE/DRY BULB TEMPERATURE',
     &'TIME PERIOD OR DISPLACEMENT (HOUR)',
     &'SURFACE WEATHER OBSERVING EQUIPMENT USED,  Code Table 9-7',
     &'DEW-POINT TEMPERATURE',
     &'WET BULB TEMPERATURE',
     &'CLOUD TYPE',
     &'CLOUD TYPE',
     &'CLOUD TYPE',
     &'CLOUD AMOUNT',
     &'HEIGHT OF BASE OF CLOUD',
     &'PRESENT WEATHER',
     &'PRESENT WEATHER',
     &'DATA SIGNIFICANCE,  Code Table 9-21  flt level termination',
     &'TIME PERIOD OR DISPLACEMENT (MINUTE)',
     &'TIME PERIOD OR DISPLACEMENT (SECOND)',
     &'LATITUDE (HIGH ACCURACY)',
     &'LONGITUDE (HIGH ACCURACY)',
     &'YEAR',
     &'MONTH',
     &'DAY',
     &'HOUR',
     &'MINUTE',
     &'SECOND',
     &'FLIGHT LEVEL PRESSURE CORRECTION,  Code Table 9-11',
     &'PRESSURE',
     &'RELATIVE HUMIDITY',
     &'SOLAR AND INFRARED RADIATION CORRECTION,  Code Table 9-13',
     &'TEMPERATURE/DRY BULB TEMPERATURE',
     &'GEOPOTENTIAL HEIGHT',
     &'LEVEL SIGNIFICANCE FOR SOUNDING,  Code Table 9-18',
     &'REASON FOR TERMINATION,  Code Table 9-17',
     &'LEVEL SIGNIFICANCE FOR SOUNDING,  Code Table 9-18',
     &'REASON FOR TERMINATION,  Code Table 9-17'/
C
      if (op19) then
        fname(17:26) = '_1Meta.txt'
        of19 = outdir(1:lendir) // fname
        open(19, file=of19, status='unknown')
        lenout = lendir + 26
        write(6, 10) of19(1:lenout)
 10     format(/'Opening O/P File:'
     &   /3x,a,'   (Metadata)')
c
c  WRITE COLUMN HEADERS ...
c
        write(19, 25) stname
 25     format('Message Type NC002019 -- Metadata, ',a/)
        
        op19 = .false.
      endif
c
 50   format(10x,i10,2x,a)
 55   format(15x,i5.5,2x,a)
c60   format(a20,a)
c     ffmt = '(f20.00,a)'
c
      write(19, 50)dsig1_19, desc(1)
      call wr19_chr(iclx1_19, desc(2))
c     chr20 = iclx1_19
c     iret = RJUST(chr20)     ! RIGHT JUSTIFY VALUE
c     write(19, 60) chr20, desc(2) 
      write(19, 50)dsig2_19, desc(3)
      call wr19_chr(iclx2_19, desc(4))
c     chr20 = iclx2_19
c     iret = RJUST(chr20)     ! RIGHT JUSTIFY VALUE
c     write(19, 60) chr20, desc(4) 
      write(19, 50)wmo19, desc(6)
      write(19, 55)wban19, desc(7)
      write(19, 50)ratp19, desc(8)
      call wr19_chr(sstn19, desc(9))
c     chr20 = sstn19
c     iret = RJUST(chr20)     ! RIGHT JUSTIFY VALUE
c     write(19, 60) chr20, desc(9) 
      call wr19_chr(obsvr19, desc(10))
c     chr20 = obsvr19
c     iret = RJUST(chr20)     ! RIGHT JUSTIFY VALUE
c     write(19, 60) chr20, desc(10) 
      call wr19_chr(SOFTV, desc(11))
c     chr20 = SOFTV  
c     iret = RJUST(chr20)     ! RIGHT JUSTIFY VALUE
c     write(19, 60) chr20, desc(11) 
      write(19, 50)nrre, desc(12)
      write(19, 50)ascn, desc(13)
      write(19, 50)rrlse, desc(14)
      call wr19_chr(RSERL, desc(15))
c     chr20 = RSERL  
c     iret = RJUST(chr20)     ! RIGHT JUSTIFY VALUE
c     write(19, 60) chr20, desc(15) 
      write(19, 50)rfreq, desc(16)
      write(19, 50)rgrsy, desc(17)
      write(19, 50)ttss, desc(18)
      write(19, 50)rrppc, desc(19)
      call wr19_fp(orcraz, '02', desc(20))
c     ffmt(6:7) = '02'
c     write(19, ffmt) orcraz, desc(20)
      call wr19_fp(orcrel, '02', desc(21))
c     write(19, ffmt) orcrel, desc(21)
      write(19, 50)psens, desc(22)
      write(19, 50)tsens, desc(23)
      write(19, 50)rhsens, desc(24)
      write(19, 50)rconf, desc(25)
      write(19, 50)bshel, desc(26)
      write(19, 50)bmfgr, desc(27)
      write(19, 50)btype, desc(28)
      call wr19_chr(BLOTN, desc(29))
c     chr20 = BLOTN  
c     iret = RJUST(chr20)     ! RIGHT JUSTIFY VALUE
c     write(19, 60) chr20, desc(29) 
      write(19, 50)bgtyp, desc(30)
      call wr19_fp(bgamt, '03', desc(31))
c     ffmt(6:7) = '03'
c     write(19, ffmt) bgamt, desc(31)
      call wr19_fp(bftln, '01', desc(32))
c     ffmt(6:7) = '01'
c     write(19, ffmt) bftln, desc(32)
      call wr19_fp(bwght, '03', desc(33))
c     ffmt(6:7) = '03'
c     write(19, ffmt) bwght, desc(33)
      write(19, 50)dsig3_19, desc(34)
      write(19, 50)b_yy, desc(35)
      write(19, 50)b_mo, desc(36)
      write(19, 50)b_dd, desc(37)
      write(19, 50)dsig4_19, desc(38)
      write(19, 50)r_yy19, desc(39)
      write(19, 50)r_mo19, desc(40)
      write(19, 50)r_dd19, desc(41)
      write(19, 50)r_hh19, desc(42)
      write(19, 50)rmin19, desc(43)
      call wr19_fp(rsec19, '02', desc(44))
c     ffmt(6:7) = '02'
c     write(19, ffmt) rsec19, desc(44)
      call wr19_fp(clat19, '05', desc(45))
c     ffmt(6:7) = '05'
c     write(19, ffmt) clat19, desc(45)
      call wr19_fp(clon19, '05', desc(46))
c     write(19, ffmt) clon19, desc(46)
      write(19, 50)hbmsl19, desc(47)
      write(19, 50)heit19, desc(48)
      write(19, 50)dsig5_19, desc(49)
      call wr19_fp(bearaz, '01', desc(50))
c     ffmt(6:7) = '01'
c     write(19, ffmt) bearaz, desc(50)
      write(19, 50) hinc, desc(51)
      call wr19_fp(dist, '01', desc(52))
c     ffmt(6:7) = '01'
c     write(19, ffmt) dist, desc(52)
      write(19, 50)dsig6_19, desc(53)
      write(19, 50)sfeqp1, desc(54)
      write(19, 50)pr_19, desc(55)
      write(19, 50)sfeqp2, desc(56)
      call wr19_fp(rh_19, '01', desc(57))
c     ffmt(6:7) = '01'
c     write(19, ffmt) rh_19, desc(57)
      write(19, 50)sfeqp3, desc(58)
      write(19, 50)wdir19, desc(59)
      call wr19_fp(wspd19, '01', desc(60))
c     ffmt(6:7) = '01'
c     write(19, ffmt) wspd19, desc(60)
      write(19, 50)sfeqp4, desc(61)
      call wr19_fp(pasttd1, '02', desc(62))
c     ffmt(6:7) = '02'
c     write(19, ffmt) pasttd1, desc(62)
      write(19, 50)tphr1, desc(63)
      call wr19_fp(pasttd2, '02', desc(64))
c     ffmt(6:7) = '02'
c     write(19, ffmt) pasttd2, desc(64)
      write(19, 50)tphr2, desc(65)
      write(19, 50)sfeqp5, desc(66)
      call wr19_fp(tdp19, '02', desc(67))
c     ffmt(6:7) = '02'
c     write(19, ffmt) tdp19, desc(67)
      call wr19_fp(tmwb, '02', desc(68))
c     write(19, ffmt) tmwb, desc(68)
      write(19, 50) cltp1, desc(69)
      write(19, 50) cltp2, desc(70)
      write(19, 50) cltp3, desc(71)
      write(19, 50) clam, desc(72)
      write(19, 50) hocb, desc(73)
      write(19, 50) prwe1, desc(74)
      write(19, 50) prwe2, desc(75)
      write(19, 50)dsig7_19, desc(76)
      write(19, 50)tpmi, desc(77)
      call wr19_fp(tpse, '02', desc(78))
c     ffmt(6:7) = '02'
c     write(19, ffmt) tpse, desc(78)
      call wr19_fp(clatterm, '05', desc(79))
c     ffmt(6:7) = '05'
c     write(19, ffmt) clatterm, desc(79)
      call wr19_fp(clonterm, '05', desc(80))
c     ffmt(6:7) = '05'
c     write(19, ffmt) clonterm, desc(80)
      write(19, 50)t_yy, desc(81)
      write(19, 50)t_mo, desc(82)
      write(19, 50)t_dd, desc(83)
      write(19, 50)t_hh, desc(84)
      write(19, 50)tmin, desc(85)
      call wr19_fp(tsec, '02', desc(86))
c     ffmt(6:7) = '02'
c     write(19, ffmt) tsec, desc(86)
      write(19, 50)flpc19, desc(87)
      write(19, 50)termpr, desc(88)
      call wr19_fp(termrh, '01', desc(89))
c     ffmt(6:7) = '01'
c     write(19, ffmt) termrh, desc(89)
      write(19, 50)termsirc, desc(90)
      call wr19_fp(term_td, '01', desc(91))
c     ffmt(6:7) = '01'
c     write(19, ffmt) term_td, desc(91)
      write(19, 50)termgph, desc(92)
      write(19, 50)termwsig, desc(93)
      write(19, 50)rtermwnd, desc(94)
      write(19, 50)termflt, desc(95)
      write(19, 50)rtermflt, desc(96)
c
      return
      end
c
c==============================================================
c
      SUBROUTINE wr19_chr (strin, desc)
      character*(*) strin, desc
      character*20 chr20
      integer RJUST
c
      chr20 = strin   
      iret = RJUST(chr20)     ! RIGHT JUSTIFY VALUE
      write(19, 60) chr20, desc 
 60   format(a20,2x,a)
c
      return
      end
c
c=============================================================
c
      SUBROUTINE wr19_fp(fpval, dec, desc)
      real fpval
      character*(*) dec, desc
      character*13 ffmt
      
      ffmt = '(f20.00,2x,a)'
      ffmt(6:7) = dec
      write(19, ffmt) fpval, desc
c
      return
      end
c
c==============================================================
c
      SUBROUTINE unpk_20(a20, tconv)                                    
      implicit none
      REAL kelvin
      PARAMETER (kelvin=273.15)
                                                                   
      integer wmo20, wban20, ratp20, dsig1_20, r_yy20, r_mo20,
     &   r_dd20, r_hh20, rmin20, hbmsl20, heit20, dsig2_20,
     &   f_yy20, f_mo20, f_dd20, f_hh20, fmin20, flpc20,
     &   pr_20, prpc20, prqc20, prqck20, rhpc20, rhqc20, rhqck20,
     &   sirc20, tdpc20, tdqc20, tdqck20 

       real rsec20, clat20, clon20, fsec20, rh_20, td_20
c
      common /msg_20/  wmo20, wban20, ratp20, dsig1_20, 
     &   r_yy20, r_mo20, r_dd20, r_hh20, rmin20, rsec20,
     &   clat20, clon20, hbmsl20, heit20, dsig2_20,
     &   f_yy20, f_mo20, f_dd20, f_hh20, fmin20, fsec20,
     &   flpc20, pr_20, prpc20, prqc20, prqck20, rh_20, rhpc20,
     &   rhqc20, rhqck20, sirc20, td_20, tdpc20, tdqc20, tdqck20
c
      CHARACTER*1 tconv
      CHARACTER*8  CVAL,PMISS                                            
      EQUIVALENCE  (RVAL,CVAL)
      REAL*8       RVAL,BMISS
      REAL*8       a20(36)
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
C
      character*100 of20
      integer lenout 
                                                                        
      DATA BMISS /   10E10  /                                                
      DATA PMISS /' MISSING'/                                            
                                                                        
C---------------------------------------------------------------------- 
C---------------------------------------------------------------------- 
C
      if (op20) then
        fname(17:26) = '_2rPTU.txt'
        of20 = outdir(1:lendir) // fname 
        open(20, file=of20, status='unknown')
        lenout = lendir + 26
        write(6, 10) of20(1:lenout)
 10     format(/'Opening O/P File:'
     &   /3x,a,'   (raw PTU,               high resolution, 1-sec)')
c
c  WRITE COLUMN HEADERS ...
c
        write(20, 25) stname 
 25     format('Message Type NC002020 -- RRS raw PTU, ',a
     &  //'  WMO  WBAN RT DS Year Mo Da Hr Mn   Sec     Lat ',
     &    '       Lon  Bar_Ht    Ht DS Year Mo Da Hr Mn   Sec',
     &    ' FLPC  Press  %C MQ Ck RawRh  %C MQ Ck SR   Td   %C MQ Ck')
c
        op20 = .false.
      endif
c
      wmo20 = 99999
      wban20 = 99999
      ratp20 = -9
      dsig1_20 = -9
      r_yy20 = 9999
      r_mo20 = 99 
      r_dd20 = 99
      r_hh20 = 99
      rmin20 = 99
      rsec20 = 99.99
      clat20 = -99.     
      clon20 = -999.     
      hbmsl20 = 99999
      heit20 = 99999
      dsig2_20 = -9
      f_yy20 = 9999
      f_mo20 = 99
      f_dd20 = 99
      f_hh20 = 99
      fmin20 = 99
      fsec20 = 99.  
      flpc20 = 999
      pr_20 = 999999
      prpc20 = -99
      prqc20 = -9
      prqck20 = -9
      rh_20 = -99. 
      rhpc20 = -99
      rhqc20 = -9
      rhqck20 = -9
      sirc20 = -9
      td_20 = 999. 
      tdpc20 = -99
      tdqc20 = -9
      tdqck20 = -9
c
c       WMO Block & Station No.
      if (a20(1) .lt. bmiss .and. a20(2) .lt. bmiss) then
       wmo20 = int(a20(1)*1000) + int(a20(2))
      endif
c
c       WBAN No.
      if (a20(3) .lt. bmiss) wban20 = int(a20(3))
c
c       Radiosonde Type
      if (a20(4) .lt. bmiss) ratp20 = int(a20(4))
c
c       Data Significance - Balloon Launch Point
      if (a20(5) .lt. bmiss) dsig1_20 = int(a20(5))
c
c       Balloon Release Year, mon, day, hr, min, sec
      if (a20(6) .lt. bmiss) r_yy20 = int(a20(6))
      if (a20(7) .lt. bmiss) r_mo20 = int(a20(7))
      if (a20(8) .lt. bmiss) r_dd20 = int(a20(8))
      if (a20(9) .lt. bmiss) r_hh20 = int(a20(9))
      if (a20(10) .lt. bmiss) rmin20 = int(a20(10))
      if (a20(11) .lt. bmiss) rsec20 = a20(11)
c
c       Latitude / Longitude
      if (a20(12) .lt. bmiss) clat20 = a20(12)
      if (a20(13) .lt. bmiss) clon20 = a20(13)
c
c       Ht Barometer Above Mean Sea Lvl
c       Height
      if (a20(14) .lt. bmiss) hbmsl20 = int(a20(14))
      if (a20(15) .lt. bmiss) heit20 = int(a20(15))
c
c       Data Significance - Flight Level Observation
      if (a20(16) .lt. bmiss) dsig2_20 = int(a20(16))
c
c       Flight Level Year, mon, day, hr, min, sec
      if (a20(17) .lt. bmiss) f_yy20 = int(a20(17))
      if (a20(18) .lt. bmiss) f_mo20 = int(a20(18))
      if (a20(19) .lt. bmiss) f_dd20 = int(a20(19))
      if (a20(20) .lt. bmiss) f_hh20 = int(a20(20))
      if (a20(21) .lt. bmiss) fmin20 = int(a20(21))
      if (a20(22) .lt. bmiss) fsec20 = a20(22)
c
c       Flight Level Pressure Correction
      if (a20(23) .lt. bmiss) flpc20 = int(a20(23))
c
c       Pressure 
      if (a20(24) .lt. bmiss) pr_20 = int(a20(24))
c
c       Data Pct Confidence, Man/Auto QC, Data Quality-Check Ind.
      if (a20(25) .lt. bmiss) prpc20 = int(a20(25))
      if (a20(26) .lt. bmiss) prqc20 = int(a20(26))
      if (a20(27) .lt. bmiss) prqck20 = int(a20(27))
c
c       Raw Relative Humidity
      if (a20(28) .lt. bmiss) rh_20 = a20(28)
c
c       Data Pct Confidence, Man/Auto QC, Data Quality-Check Ind.
      if (a20(29) .lt. bmiss) rhpc20 = int(a20(29))
      if (a20(30) .lt. bmiss) rhqc20 = int(a20(30))
      if (a20(31) .lt. bmiss) rhqck20 = int(a20(31))
c
c       Solar & Infrared Rad. Corr.
      if (a20(32) .lt. bmiss) sirc20 = int(a20(32))
c
c       Temperature/Dry Bulb Temperature                
      if (a20(33) .lt. bmiss) then
        if (tconv .eq. 'K') then
           td_20 = a20(33)
        else
           td_20 = a20(33) - kelvin
        endif
      endif
c
c       Data Pct Confidence, Man/Auto QC, Data Quality-Check Ind.
      if (a20(34) .lt. bmiss) tdpc20 = int(a20(34))
      if (a20(35) .lt. bmiss) tdqc20 = int(a20(35))
      if (a20(36) .lt. bmiss) tdqck20 = int(a20(36))
c
      write(20, 100) wmo20, wban20, ratp20, dsig1_20, 
     &   r_yy20, r_mo20, r_dd20, r_hh20, rmin20, rsec20,
     &   clat20, clon20, hbmsl20, heit20, dsig2_20,
     &   f_yy20, f_mo20, f_dd20, f_hh20, fmin20, fsec20,
     &   flpc20, pr_20, prpc20, prqc20, prqck20, rh_20, rhpc20,
     &   rhqc20, rhqck20, sirc20, td_20, tdpc20, tdqc20, tdqck20 
 100  format(i5.5,1x,i5.5,1x,i2,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,f9.5,1x,f10.5,1x,i5,1x,i5,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,i4,1x,i6,1x,i3,1x,i2,1x,i2,1x,f5.1,1x,i3,
     &   1x,i2,1x,i2,1x,i2,1x,f5.1,1x,i3,1x,i2,1x,i2)
c
      RETURN                                                            
      END                                                               
C
C========================================================
C
      SUBROUTINE unpk_21(a21)                                    
      implicit none
                                                                      
      integer wmo21, wban21, ratp21, dsig1_21, r_yy21, r_mo21,
     &   r_dd21, r_hh21, rmin21, hbmsl21, heit21, dsig2_21,
     &   f_yy21, f_mo21, f_dd21, f_hh21, fmin21, 
     &   latmq21, latck21, lonmq21, lonck21, gps_ht21, htmq21, htck21,
     &   uwmq21, uwck21, vwmq21, vwck21, pccf21

       real rsec21, clat21, clon21, fsec21, gpslat21, gpslon21,
     &   uwnd21, vwnd21
c
      common /msg_21/  wmo21, wban21, ratp21, dsig1_21, 
     &   r_yy21, r_mo21, r_dd21, r_hh21, rmin21, rsec21,
     &   clat21, clon21, hbmsl21, heit21, dsig2_21,
     &   f_yy21, f_mo21, f_dd21, f_hh21, fmin21, fsec21,
     &   gpslat21, latmq21, latck21, gpslon21, lonmq21, lonck21, 
     &   gps_ht21, htmq21, htck21,
     &   uwnd21, uwmq21, uwck21, vwnd21, vwmq21, vwck21, pccf21
c
      CHARACTER*8  CVAL,PMISS                                            
      EQUIVALENCE  (RVAL,CVAL)
      REAL*8       RVAL,BMISS
      REAL*8       a21(38)
      integer      lenout
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
C
      character*100 of21
                                                                        
      DATA BMISS /   10E10  /                                                
      DATA PMISS /' MISSING'/                                            
                                                                        
C---------------------------------------------------------------------- 
C---------------------------------------------------------------------- 
C
      if (op21) then
        fname(17:26) = '_3GPSu.txt'
        of21 = outdir(1:lendir) // fname 
        open(21, file=of21, status='unknown')
        lenout = lendir + 26
        write(6, 10) of21(1:lenout)
 10     format(/'Opening O/P File:'
     &   /3x,a,'   (raw GPS unsmoothed,    high resolution, 1-sec)')
c
c  WRITE COLUMN HEADERS ...
c
        write(21, 25) stname
 25     format('Message Type NC002021 -- RRS raw GPS unsmoothed, ',a
     &  //'  WMO  WBAN RT DS Year Mo Da Hr Mn   Sec      Lat ',
     &    '       Lon Bar_Ht    Ht DS Year Mo Da Hr Mn   Sec',
     &    '   GPS-Lat MQ Ck    GPS-Lon MQ Ck GP_HT MQ Ck',
     &    '  U-Wnd MQ Ck  V-Wnd MQ Ck  %C')
C
        op21 = .false.
      endif
c
      wmo21 = 99999
      wban21 = 99999
      ratp21 = -9
      dsig1_21 = -9
      r_yy21 = 9999
      r_mo21 = 99 
      r_dd21 = 99
      r_hh21 = 99
      rmin21 = 99
      rsec21 = 99.  
      clat21 = -99.     
      clon21 = -999.     
      hbmsl21 = 99999
      heit21 = 99999
      dsig2_21 = -9
      f_yy21 = 9999
      f_mo21 = 99
      f_dd21 = 99
      f_hh21 = 99
      fmin21 = 99
      fsec21 = 99.  
      gpslat21 = -99.     
      latmq21 = -9
      latck21 = -9
      gpslon21 = -999.     
      lonmq21 = -9
      lonck21 = -9
      gps_ht21 = 99999
      htmq21 = -9
      htck21 = -9
      uwnd21 = -999. 
      uwmq21 = -9
      uwck21 = -9
      vwnd21 = -999. 
      vwmq21 = -9
      vwck21 = -9
      pccf21 = -99
c
c       WMO Block & Station No.
      if (a21(1) .lt. bmiss .and. a21(2) .lt. bmiss) then
       wmo21 = int(a21(1)*1000) + int(a21(2))
      endif
c
c       WBAN No.
      if (a21(3) .lt. bmiss) wban21 = int(a21(3))
c
c       Radiosonde Type
      if (a21(4) .lt. bmiss) ratp21 = int(a21(4))
c
c       Data Significance - Balloon Launch Point
      if (a21(5) .lt. bmiss) dsig1_21 = int(a21(5))
c
c       Balloon Release Year, mon, day, hr, min, sec
      if (a21(6) .lt. bmiss) r_yy21 = int(a21(6))
      if (a21(7) .lt. bmiss) r_mo21 = int(a21(7))
      if (a21(8) .lt. bmiss) r_dd21 = int(a21(8))
      if (a21(9) .lt. bmiss) r_hh21 = int(a21(9))
      if (a21(10) .lt. bmiss) rmin21 = int(a21(10))
      if (a21(11) .lt. bmiss) rsec21 = a21(11)
c
c       Latitude / Longitude
      if (a21(12) .lt. bmiss) clat21 = a21(12)
      if (a21(13) .lt. bmiss) clon21 = a21(13)
c
c       Ht Barometer Above Mean Sea Lvl
c       Height
      if (a21(14) .lt. bmiss) hbmsl21 = int(a21(14))
      if (a21(15) .lt. bmiss) heit21 = int(a21(15))
c
c       Data Significance - Flight Level Observation
      if (a21(16) .lt. bmiss) dsig2_21 = int(a21(16))
c
c       Flight Level Year, mon, day, hr, min, sec
      if (a21(17) .lt. bmiss) f_yy21 = int(a21(17))
      if (a21(18) .lt. bmiss) f_mo21 = int(a21(18))
      if (a21(19) .lt. bmiss) f_dd21 = int(a21(19))
      if (a21(20) .lt. bmiss) f_hh21 = int(a21(20))
      if (a21(21) .lt. bmiss) fmin21 = int(a21(21))
      if (a21(22) .lt. bmiss) fsec21 = a21(22)
c
c       GPS Latitude
      if (a21(23) .lt. bmiss) gpslat21 = a21(23)
c
c       GPS Latitude Man/Auto QC, Data Quality-Check Ind.
      if (a21(24) .lt. bmiss) latmq21 = int(a21(24))
      if (a21(25) .lt. bmiss) latck21 = int(a21(25))
c
c       GPS Longitude
      if (a21(26) .lt. bmiss) gpslon21 = a21(26)
c
c       GPS Longitude Man/Auto QC, Data Quality-Check Ind.
      if (a21(27) .lt. bmiss) lonmq21 = int(a21(27))
      if (a21(28) .lt. bmiss) lonck21 = int(a21(28))
c
c       GPS Height   
      if (a21(29) .lt. bmiss) gps_ht21 = a21(29)
c
c       GPS Height Man/Auto QC, Data Quality-Check Ind.
      if (a21(30) .lt. bmiss) htmq21 = int(a21(30))
      if (a21(31) .lt. bmiss) htck21 = int(a21(31))
c
c       GPS u wind Component
      if (a21(32) .lt. bmiss) uwnd21 = a21(32)
c
c       GPS u wind Component Man/Auto QC, Data Quality-Check Ind.
      if (a21(33) .lt. bmiss) uwmq21 = int(a21(33))
      if (a21(34) .lt. bmiss) uwck21 = int(a21(34))
c
c       GPS v wind Component
      if (a21(35) .lt. bmiss) vwnd21 = a21(35)
c
c       GPS v wind Component Man/Auto QC, Data Quality-Check Ind.
      if (a21(36) .lt. bmiss) vwmq21 = int(a21(36))
      if (a21(37) .lt. bmiss) vwck21 = int(a21(37))
c
c       Data Percent Confidence
      if (a21(38) .lt. bmiss) pccf21 = int(a21(38))
c
      write(21, 100) wmo21, wban21, ratp21, dsig1_21, 
     &   r_yy21, r_mo21, r_dd21, r_hh21, rmin21, rsec21,
     &   clat21, clon21, hbmsl21, heit21, dsig2_21,
     &   f_yy21, f_mo21, f_dd21, f_hh21, fmin21, fsec21,
     &   gpslat21, latmq21, latck21, gpslon21, lonmq21, lonck21, 
     &   gps_ht21, htmq21, htck21,
     &   uwnd21, uwmq21, uwck21, vwnd21, vwmq21, vwck21, pccf21
 100  format(i5.5,1x,i5.5,1x,i2,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,f9.5,1x,f10.5,1x,i5,1x,i5,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,f9.5,1x,i2,1x,i2,1x,f10.5,1x,i2,1x,i2,
     &   1x,i5,1x,i2,1x,i2,
     &   1x,f6.1,1x,i2,1x,i2,1x,f6.1,1x,i2,1x,i2,1x,i3)
c
      RETURN                                                            
      END
C
C========================================================
C
      SUBROUTINE unpk_22(a22)                                    
      implicit none
                                                                     
      integer wmo22, wban22, ratp22, dsig1_22, r_yy22, r_mo22,
     &   r_dd22, r_hh22, rmin22, hbmsl22, heit22, dsig2_22,
     &   f_yy22, f_mo22, f_dd22, f_hh22, fmin22, 
     &   latmq22, latck22, lonmq22, lonck22, gps_ht22, htmq22, htck22,
     &   uwmq22, uwck22, vwmq22, vwck22, pccf22

       real rsec22, clat22, clon22, fsec22, gpslat22, gpslon22,
     &   uwnd22, vwnd22
c
      common /msg_22/  wmo22, wban22, ratp22, dsig1_22, 
     &   r_yy22, r_mo22, r_dd22, r_hh22, rmin22, rsec22,
     &   clat22, clon22, hbmsl22, heit22, dsig2_22,
     &   f_yy22, f_mo22, f_dd22, f_hh22, fmin22, fsec22,
     &   gpslat22, latmq22, latck22, gpslon22, lonmq22, lonck22, 
     &   gps_ht22, htmq22, htck22,
     &   uwnd22, uwmq22, uwck22, vwnd22, vwmq22, vwck22, pccf22
c
      CHARACTER*8  CVAL,PMISS                                            
      EQUIVALENCE  (RVAL,CVAL)
      REAL*8       RVAL,BMISS
      REAL*8       a22(38)
      integer      lenout
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
C
      character*100 of22
                                                                        
      DATA BMISS /   10E10  /                                                
      DATA PMISS /' MISSING'/                                            
                                                                        
C---------------------------------------------------------------------- 
C---------------------------------------------------------------------- 
C
      if (op22) then
        fname(17:26) = '_4GPSs.txt'
        of22 = outdir(1:lendir) // fname 
        open(22, file=of22, status='unknown')
        lenout = lendir + 26
        write(6, 10) of22(1:lenout)
 10     format(/'Opening O/P File:'
     &   /3x,a,'   (raw GPS smoothed,      high resolution, 1-sec)')
c
c  WRITE COLUMN HEADERS ...
c
        write(22, 25) stname
 25      format('Message Type NC002022 -- RRS raw GPS smoothed, ',a
     &  //'  WMO  WBAN RT DS Year Mo Da Hr Mn   Sec      Lat ',
     &    '       Lon Bar_Ht    Ht DS Year Mo Da Hr Mn   Sec',
     &    '   GPS-Lat MQ Ck    GPS-Lon MQ Ck GP_HT MQ Ck',
     &    '  U-Wnd MQ Ck  V-Wnd MQ Ck  %C')
C
        op22 = .false.
      endif
c
      wmo22 = 99999
      wban22 = 99999
      ratp22 = -9
      dsig1_22 = -9
      r_yy22 = 9999
      r_mo22 = 99 
      r_dd22 = 99
      r_hh22 = 99
      rmin22 = 99
      rsec22 = 99.  
      clat22 = -99.     
      clon22 = -999.     
      hbmsl22 = 99999
      heit22 = 99999
      dsig2_22 = -9
      f_yy22 = 9999
      f_mo22 = 99
      f_dd22 = 99
      f_hh22 = 99
      fmin22 = 99
      fsec22 = 99.  
      gpslat22 = -99.     
      latmq22 = -9
      latck22 = -9
      gpslon22 = -999.     
      lonmq22 = -9
      lonck22 = -9
      gps_ht22 = 99999
      htmq22 = -9
      htck22 = -9
      uwnd22 = -999. 
      uwmq22 = -9
      uwck22 = -9
      vwnd22 = -999. 
      vwmq22 = -9
      vwck22 = -9
      pccf22 = -99
c
c       WMO Block & Station No.
      if (a22(1) .lt. bmiss .and. a22(2) .lt. bmiss) then
       wmo22 = int(a22(1)*1000) + int(a22(2))
      endif
c
c       WBAN No.
      if (a22(3) .lt. bmiss) wban22 = int(a22(3))
c
c       Radiosonde Type
      if (a22(4) .lt. bmiss) ratp22 = int(a22(4))
c
c       Data Significance - Balloon Launch Point
      if (a22(5) .lt. bmiss) dsig1_22 = int(a22(5))
c
c       Balloon Release Year, mon, day, hr, min, sec
      if (a22(6) .lt. bmiss) r_yy22 = int(a22(6))
      if (a22(7) .lt. bmiss) r_mo22 = int(a22(7))
      if (a22(8) .lt. bmiss) r_dd22 = int(a22(8))
      if (a22(9) .lt. bmiss) r_hh22 = int(a22(9))
      if (a22(10) .lt. bmiss) rmin22 = int(a22(10))
      if (a22(11) .lt. bmiss) rsec22 = a22(11)
c
c       Latitude / Longitude
      if (a22(12) .lt. bmiss) clat22 = a22(12)
      if (a22(13) .lt. bmiss) clon22 = a22(13)
c
c       Ht Barometer Above Mean Sea Lvl
c       Height
      if (a22(14) .lt. bmiss) hbmsl22 = int(a22(14))
      if (a22(15) .lt. bmiss) heit22 = int(a22(15))
c
c       Data Significance - Flight Level Observation
      if (a22(16) .lt. bmiss) dsig2_22 = int(a22(16))
c
c       Flight Level Year, mon, day, hr, min, sec
      if (a22(17) .lt. bmiss) f_yy22 = int(a22(17))
      if (a22(18) .lt. bmiss) f_mo22 = int(a22(18))
      if (a22(19) .lt. bmiss) f_dd22 = int(a22(19))
      if (a22(20) .lt. bmiss) f_hh22 = int(a22(20))
      if (a22(21) .lt. bmiss) fmin22 = int(a22(21))
      if (a22(22) .lt. bmiss) fsec22 = a22(22)
c
c       GPS Latitude
      if (a22(23) .lt. bmiss) gpslat22 = a22(23)
c
c       GPS Latitude Man/Auto QC, Data Quality-Check Ind.
      if (a22(24) .lt. bmiss) latmq22 = int(a22(24))
      if (a22(25) .lt. bmiss) latck22 = int(a22(25))
c
c       GPS Longitude
      if (a22(26) .lt. bmiss) gpslon22 = a22(26)
c
c       GPS Longitude Man/Auto QC, Data Quality-Check Ind.
      if (a22(27) .lt. bmiss) lonmq22 = int(a22(27))
      if (a22(28) .lt. bmiss) lonck22 = int(a22(28))
c
c       GPS Height   
      if (a22(29) .lt. bmiss) gps_ht22 = a22(29)
c
c       GPS Height Man/Auto QC, Data Quality-Check Ind.
      if (a22(30) .lt. bmiss) htmq22 = int(a22(30))
      if (a22(31) .lt. bmiss) htck22 = int(a22(31))
c
c       GPS u wind Component
      if (a22(32) .lt. bmiss) uwnd22 = a22(32)
c
c       GPS u wind Component Man/Auto QC, Data Quality-Check Ind.
      if (a22(33) .lt. bmiss) uwmq22 = int(a22(33))
      if (a22(34) .lt. bmiss) uwck22 = int(a22(34))
c
c       GPS v wind Component
      if (a22(35) .lt. bmiss) vwnd22 = a22(35)
c
c       GPS v wind Component Man/Auto QC, Data Quality-Check Ind.
      if (a22(36) .lt. bmiss) vwmq22 = int(a22(36))
      if (a22(37) .lt. bmiss) vwck22 = int(a22(37))
c
c       Data Percent Confidence
      if (a22(38) .lt. bmiss) pccf22 = int(a22(38))
c
      write(22, 100) wmo22, wban22, ratp22, dsig1_22, 
     &   r_yy22, r_mo22, r_dd22, r_hh22, rmin22, rsec22,
     &   clat22, clon22, hbmsl22, heit22, dsig2_22,
     &   f_yy22, f_mo22, f_dd22, f_hh22, fmin22, fsec22,
     &   gpslat22, latmq22, latck22, gpslon22, lonmq22, lonck22, 
     &   gps_ht22, htmq22, htck22,
     &   uwnd22, uwmq22, uwck22, vwnd22, vwmq22, vwck22, pccf22
 100  format(i5.5,1x,i5.5,1x,i2,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,f9.5,1x,f10.5,1x,i5,1x,i5,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,f9.5,1x,i2,1x,i2,1x,f10.5,1x,i2,1x,i2,
     &   1x,i5,1x,i2,1x,i2,
     &   1x,f6.1,1x,i2,1x,i2,1x,f6.1,1x,i2,1x,i2,1x,i3)
c
      RETURN                                                            
      END
C
C========================================================
C
      SUBROUTINE unpk_23(a23, tconv)                               
c
      implicit none
      REAL kelvin
      PARAMETER (kelvin=273.15)
c
c     COMMON Data Definitions..                              
      integer wmo23, wban23, ratp23, dsig1_23, r_yy23, r_mo23,
     &   r_dd23, r_hh23, rmin23, hbmsl23, heit23, dsig2_23,
     &   f_yy23, f_mo23, f_dd23, f_hh23, fmin23, flpc1_23, pr1_23,
     &   pr1maqc, pr1qcck, flpc2_23, pr2_23, pr2maqc, pr2qcck,
     &   rh_maqc, rh_qcck, sirc1_23, td1_maqc, td1_qcck, sirc2_23,
     &   td2_maqc, td2_qcck, tdp_maqc,
     &   tdp_qcck, gpht23, gpht_maqc, gpht_qcck 

       real rsec23, clat23, clon23, fsec23, rh_23, td1_23, td2_23, 
     &  tdp_23
c
      common /hi_res_ptu/ wmo23, wban23, ratp23, dsig1_23, r_yy23, 
     &   r_mo23, r_dd23, r_hh23, rmin23, hbmsl23, heit23, dsig2_23,
     &   f_yy23, f_mo23, f_dd23, f_hh23, fmin23, flpc1_23, pr1_23,
     &   pr1maqc, pr1qcck, flpc2_23, pr2_23, pr2maqc, pr2qcck,
     &   rh_maqc, rh_qcck, sirc1_23, td1_maqc, td1_qcck, sirc2_23,
     &   td2_maqc, td2_qcck, tdp_maqc,
     &   tdp_qcck, gpht23, gpht_maqc, gpht_qcck,
     &   rsec23, clat23, clon23, fsec23, rh_23, td1_23, td2_23, tdp_23
c
      CHARACTER*1 tconv
      CHARACTER*8  CVAL,PMISS                                           
      EQUIVALENCE  (RVAL,CVAL)
      REAL*8       RVAL,BMISS
      REAL*8       a23(47)
      integer      lenout
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
C
      character*100 of23
                                                                        
      DATA BMISS /   10E10  /                                                
      DATA PMISS /' MISSING'/                                            
                                                                        
C---------------------------------------------------------------------- 
C---------------------------------------------------------------------- 
C
      if (op23) then
        fname(17:26) = '_5pPTU.txt'
        of23 = outdir(1:lendir) // fname 
        open(23, file=of23, status='unknown')
        lenout = lendir + 26
        write(6, 10) of23(1:lenout)
 10     format(/'Opening O/P File:'
     &   /3x,a,'   (processed PTU,         high resolution, 1-sec)')
c
c  WRITE COLUMN HEADERS ...
c
        write(23, 25) stname
 25     format('Message Type NC002023 -- RRS processed PTU, ',a
     &  //'  WMO  WBAN RT DS Year Mo Da Hr Mn   Sec      Lat ',
     &    '       Lon Bar_Ht    Ht DS Year Mo Da Hr Mn   Sec',
     &    ' FLPC  Press MQ Ck FLPC  Press MQ Ck    Rh MQ Ck',
     &    ' SR   Td  MQ Ck SR   Td  MQ Ck   DP  MQ Ck  GPHT MQ Ck')
C
        op23 = .false.
      endif
c
      wmo23 = 99999
      wban23 = 99999
      ratp23 = -9
      dsig1_23 = -9
      r_yy23 = 9999
      r_mo23 = 99 
      r_dd23 = 99
      r_hh23 = 99
      rmin23 = 99
      rsec23 = 99.  
      clat23 = -99.     
      clon23 = -999.     
      hbmsl23 = 99999
      heit23 = 99999
      dsig2_23 = -9
      f_yy23 = 9999
      f_mo23 = 99
      f_dd23 = 99
      f_hh23 = 99
      fmin23 = 99
      fsec23 = 99.  
      flpc1_23 = 999
      pr1_23 = 999999
      pr1maqc = -9
      pr1qcck = -9
      flpc2_23 = 999
      pr2_23 = 999999
      pr2maqc = -9
      pr2qcck = -9
      rh_23 = -99. 
      rh_maqc = -9
      rh_qcck = -9
      sirc1_23 = -9
      td1_23 = 999. 
      td1_maqc = -9
      td1_qcck = -9
      sirc2_23 = -9
      td2_23 = 999. 
      td2_maqc = -9
      td2_qcck = -9
      tdp_23 = 999. 
      tdp_maqc = -9
      tdp_qcck = -9
      gpht23 = 99999
      gpht_maqc = -9
      gpht_qcck = -9
c
c       WMO Block & Station No.
      if (a23(1) .lt. bmiss .and. a23(2) .lt. bmiss) then
       wmo23 = int(a23(1)*1000) + int(a23(2))
      endif
c       WBAN No.
      if (a23(3) .lt. bmiss) wban23 = int(a23(3))
c
c       Radiosonde Type
      if (a23(4) .lt. bmiss) ratp23 = int(a23(4))
c
c       Data Significance
      if (a23(5) .lt. bmiss) dsig1_23 = int(a23(5))
c
c       Balloon Release Year, mon, day, hr, min, sec
      if (a23(6) .lt. bmiss) r_yy23 = int(a23(6))
      if (a23(7) .lt. bmiss) r_mo23 = int(a23(7))
      if (a23(8) .lt. bmiss) r_dd23 = int(a23(8))
      if (a23(9) .lt. bmiss) r_hh23 = int(a23(9))
      if (a23(10) .lt. bmiss) rmin23 = int(a23(10))
      if (a23(11) .lt. bmiss) rsec23 = a23(11)
c
c       Latitude / Longitude
      if (a23(12) .lt. bmiss) clat23 = a23(12)
      if (a23(13) .lt. bmiss) clon23 = a23(13)
c
c       Ht Barometer Above Mean Sea Lvl
c       Height
      if (a23(14) .lt. bmiss) hbmsl23 = int(a23(14))
      if (a23(15) .lt. bmiss) heit23 = int(a23(15))
c
c       Data Significance
      if (a23(16) .lt. bmiss) dsig2_23 = int(a23(16))
c
c       Flight Level Year, mon, day, hr, min, sec
      if (a23(17) .lt. bmiss) f_yy23 = int(a23(17))
      if (a23(18) .lt. bmiss) f_mo23 = int(a23(18))
      if (a23(19) .lt. bmiss) f_dd23 = int(a23(19))
      if (a23(20) .lt. bmiss) f_hh23 = int(a23(20))
      if (a23(21) .lt. bmiss) fmin23 = int(a23(21))
      if (a23(22) .lt. bmiss) fsec23 = a23(22)
c
c       Flt level Pressure Correction 
      if (a23(23) .lt. bmiss) flpc1_23 = int(a23(23))
c
c       Corrected Pressure 
      if (a23(24) .lt. bmiss) pr1_23 = int(a23(24))
c
c       Corrected Pressure - MAQC 
      if (a23(25) .lt. bmiss) pr1maqc = int(a23(25))
c
c       Corrected Pressure - QC CHECK
      if (a23(26) .lt. bmiss) pr1qcck = int(a23(26))
c
c       Flt level Pressure Correction (smoothed) 
      if (a23(27) .lt. bmiss) flpc2_23 = int(a23(27))
c
c       Smoothed Pressure 
      if (a23(28) .lt. bmiss) pr2_23 = int(a23(28))
c
c       Smoothed Pressure - MAQC 
      if (a23(29) .lt. bmiss) pr2maqc = int(a23(29))
c
c       Smoothed Pressure - QC CHECK
      if (a23(30) .lt. bmiss) pr2qcck = int(a23(30))
c
c       Corrected Relative Humidity
      if (a23(31) .lt. bmiss) rh_23 = a23(31)
c
c       Corrected RH - MAQC 
      if (a23(32) .lt. bmiss) rh_maqc = int(a23(32))
c
c       Corrected RH - QC CHECK
      if (a23(33) .lt. bmiss) rh_qcck = int(a23(33))
c
c       Solar & Infrared Rad. Corr. (Uncorrected Temperature)
      if (a23(34) .lt. bmiss) sirc1_23 = int(a23(34))
c
c       Uncorrected Temperature                
      if (a23(35) .lt. bmiss) then
        if (tconv .eq. 'K') then
           td1_23 = a23(35)
        else
           td1_23 = a23(35) - kelvin
        endif
      endif
c
c       Uncorrected Temp. - MAQC 
      if (a23(36) .lt. bmiss) td1_maqc = int(a23(36))
c
c       Uncorrected Temp. - QC CHECK
      if (a23(37) .lt. bmiss) td1_qcck = int(a23(37))
c
c       Solar & Infrared Rad. Corr. (Corrected Temperature)
      if (a23(38) .lt. bmiss) sirc2_23 = int(a23(38))
c
c       Corrected Temperature                
      if (a23(39) .lt. bmiss) then
        if (tconv .eq. 'K') then
           td2_23 = a23(39)
        else
           td2_23 = a23(39) - kelvin
        endif
      endif
c
c       Corrected Temp. - MAQC 
      if (a23(40) .lt. bmiss) td2_maqc = int(a23(40))
c
c       Corrected Temp. - QC CHECK
      if (a23(41) .lt. bmiss) td2_qcck = int(a23(41))
c
c       Derived Dew Pt. Temperature                
      if (a23(42) .lt. bmiss) then
        if (tconv .eq. 'K') then
           tdp_23 = a23(42)
        else
           tdp_23 = a23(42) - kelvin
        endif
      endif
c
c       Dew Point Temp. - MAQC 
      if (a23(43) .lt. bmiss) tdp_maqc = int(a23(43))
c
c       Dew Point Temp. - QC CHECK
      if (a23(44) .lt. bmiss) tdp_qcck = int(a23(44))
c
c       Derived Geopotential Height                
      if (a23(45) .lt. bmiss) gpht23 = int(a23(45))
c
c       Dew Point Temp. - MAQC 
      if (a23(46) .lt. bmiss) gpht_maqc = int(a23(46))
c
c       Dew Point Temp. - QC CHECK
      if (a23(47) .lt. bmiss) gpht_qcck = int(a23(47))
c
      write(23, 100) wmo23, wban23, ratp23, dsig1_23, 
     &  r_yy23, r_mo23, r_dd23, r_hh23, rmin23, rsec23, 
     &  clat23, clon23, hbmsl23, heit23, dsig2_23, 
     &  f_yy23, f_mo23, f_dd23, f_hh23, fmin23, fsec23, 
     &  flpc1_23, pr1_23, pr1maqc, pr1qcck, 
     &  flpc2_23, pr2_23, pr2maqc, pr2qcck, rh_23, rh_maqc, rh_qcck, 
     &  sirc1_23, td1_23, td1_maqc, td1_qcck, 
     &  sirc2_23, td2_23, td2_maqc, td2_qcck, 
     &  tdp_23, tdp_maqc, tdp_qcck, gpht23, gpht_maqc, gpht_qcck

 100  format(i5.5,1x,i5.5,1x,i2,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,f9.5,1x,f10.5,1x,i5,1x,i5,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,i4,1x,i6,1x,i2,1x,i2,
     &   1x,i4,1x,i6,1x,i2,1x,i2,1x,f5.1,1x,i2,1x,i2,
     &   1x,i2,1x,f5.1,1x,i2,1x,i2,
     &   1x,i2,1x,f5.1,1x,i2,1x,i2,
     &   1x,f5.1,1x,i2,1x,i2,1x,i5,1x,i2,1x,i2)
c
      RETURN 
      END
C
C========================================================
C
      SUBROUTINE unpk_24(a24)                                    
      implicit none
                                                                       
      integer wmo24, wban24, ratp24, dsig1_24, r_yy24, r_mo24,
     &   r_dd24, r_hh24, rmin24, hbmsl24, heit24, dsig2_24,
     &   f_yy24, f_mo24, f_dd24, f_hh24, fmin24, 
     &   latmq24, latck24, lonmq24, lonck24, gps_ht24, htmq24, htck24,
     &   uwmq24, uwck24, vwmq24, vwck24

       real rsec24, clat24, clon24, fsec24, gpslat24, gpslon24,
     &   uwnd24, vwnd24
c
      common /msg_24/  wmo24, wban24, ratp24, dsig1_24, 
     &   r_yy24, r_mo24, r_dd24, r_hh24, rmin24, rsec24,
     &   clat24, clon24, hbmsl24, heit24, dsig2_24,
     &   f_yy24, f_mo24, f_dd24, f_hh24, fmin24, fsec24,
     &   gpslat24, latmq24, latck24, gpslon24, lonmq24, lonck24, 
     &   gps_ht24, htmq24, htck24,
     &   uwnd24, uwmq24, uwck24, vwnd24, vwmq24, vwck24
c
      CHARACTER*8  CVAL,PMISS                                            
      EQUIVALENCE  (RVAL,CVAL)
      REAL*8       RVAL,BMISS
      REAL*8       a24(37)
      integer      lenout
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
C
      character*100 of24
                                                                        
      DATA BMISS /   10E10  /                                                
      DATA PMISS /' MISSING'/                                            
                                                                        
C---------------------------------------------------------------------- 
C---------------------------------------------------------------------- 
C
      if (op24) then
        fname(17:26) = '_6pGPS.txt'
        of24 = outdir(1:lendir) // fname 
        open(24, file=of24, status='unknown')
        lenout = lendir + 26
        write(6, 10) of24(1:lenout)
 10     format(/'Opening O/P File:'
     &   /3x,a,'   (processed GPS,         high resolution, 1-sec)')
c
c  WRITE COLUMN HEADERS ...
c
        write(24, 25) stname
 25     format('Message Type NC002024 -- RRS processed GPS, ',a
     &  //'  WMO  WBAN RT DS Year Mo Da Hr Mn   Sec      Lat ',
     &    '       Lon Bar_Ht    Ht DS Year Mo Da Hr Mn   Sec',
     &    '   GPS-Lat MQ Ck    GPS-Lon MQ Ck GP_HT MQ Ck',
     &    '  U-Wnd MQ Ck  V-Wnd MQ Ck')
C
        op24 = .false.
      endif
      wmo24 = 99999
      wban24 = 99999
      ratp24 = -9
      dsig1_24 = -9
      r_yy24 = 9999
      r_mo24 = 99 
      r_dd24 = 99
      r_hh24 = 99
      rmin24 = 99
      rsec24 = 99.  
      clat24 = -99.     
      clon24 = -999.     
      hbmsl24 = 99999
      heit24 = 99999
      dsig2_24 = -9
      f_yy24 = 9999
      f_mo24 = 99
      f_dd24 = 99
      f_hh24 = 99
      fmin24 = 99
      fsec24 = 99.     
      gpslat24 = -99.     
      latmq24 = -9
      latck24 = -9
      gpslon24 = -999.     
      lonmq24 = -9
      lonck24 = -9
      gps_ht24 = 99999
      htmq24 = -9
      htck24 = -9
      uwnd24 = -999.     
      uwmq24 = -9
      uwck24 = -9
      vwnd24 = -999.     
      vwmq24 = -9
      vwck24 = -9
c
c       WMO Block & Station No.
      if (a24(1) .lt. bmiss .and. a24(2) .lt. bmiss) then
       wmo24 = int(a24(1)*1000) + int(a24(2))
      endif
c
c       WBAN No.
      if (a24(3) .lt. bmiss) wban24 = int(a24(3))
c
c       Radiosonde Type
      if (a24(4) .lt. bmiss) ratp24 = int(a24(4))
c
c       Data Significance - Balloon Launch Point
      if (a24(5) .lt. bmiss) dsig1_24 = int(a24(5))
c
c       Balloon Release Year, mon, day, hr, min, sec
      if (a24(6) .lt. bmiss) r_yy24 = int(a24(6))
      if (a24(7) .lt. bmiss) r_mo24 = int(a24(7))
      if (a24(8) .lt. bmiss) r_dd24 = int(a24(8))
      if (a24(9) .lt. bmiss) r_hh24 = int(a24(9))
      if (a24(10) .lt. bmiss) rmin24 = int(a24(10))
      if (a24(11) .lt. bmiss) rsec24 = a24(11)
c
c       Latitude / Longitude
      if (a24(12) .lt. bmiss) clat24 = a24(12)
      if (a24(13) .lt. bmiss) clon24 = a24(13)
c
c       Ht Barometer Above Mean Sea Lvl
c       Height
      if (a24(14) .lt. bmiss) hbmsl24 = int(a24(14))
      if (a24(15) .lt. bmiss) heit24 = int(a24(15))
c
c       Data Significance - Flight Level Observation
      if (a24(16) .lt. bmiss) dsig2_24 = int(a24(16))
c
c       Flight Level Year, mon, day, hr, min, sec
      if (a24(17) .lt. bmiss) f_yy24 = int(a24(17))
      if (a24(18) .lt. bmiss) f_mo24 = int(a24(18))
      if (a24(19) .lt. bmiss) f_dd24 = int(a24(19))
      if (a24(20) .lt. bmiss) f_hh24 = int(a24(20))
      if (a24(21) .lt. bmiss) fmin24 = int(a24(21))
      if (a24(22) .lt. bmiss) fsec24 = a24(22)
c
c       GPS Latitude
      if (a24(23) .lt. bmiss) gpslat24 = a24(23)
c
c       GPS Latitude Man/Auto QC, Data Quality-Check Ind.
      if (a24(24) .lt. bmiss) latmq24 = int(a24(24))
      if (a24(25) .lt. bmiss) latck24 = int(a24(25))
c
c       GPS Longitude
      if (a24(26) .lt. bmiss) gpslon24 = a24(26)
c
c       GPS Longitude Man/Auto QC, Data Quality-Check Ind.
      if (a24(27) .lt. bmiss) lonmq24 = int(a24(27))
      if (a24(28) .lt. bmiss) lonck24 = int(a24(28))
c
c       GPS Height   
      if (a24(29) .lt. bmiss) gps_ht24 = a24(29)
c
c       GPS Height Man/Auto QC, Data Quality-Check Ind.
      if (a24(30) .lt. bmiss) htmq24 = int(a24(30))
      if (a24(31) .lt. bmiss) htck24 = int(a24(31))
c
c       GPS u wind Component
      if (a24(32) .lt. bmiss) uwnd24 = a24(32)
c
c       GPS u wind Component Man/Auto QC, Data Quality-Check Ind.
      if (a24(33) .lt. bmiss) uwmq24 = int(a24(33))
      if (a24(34) .lt. bmiss) uwck24 = int(a24(34))
c
c       GPS v wind Component
      if (a24(35) .lt. bmiss) vwnd24 = a24(35)
c
c       GPS v wind Component Man/Auto QC, Data Quality-Check Ind.
      if (a24(36) .lt. bmiss) vwmq24 = int(a24(36))
      if (a24(37) .lt. bmiss) vwck24 = int(a24(37))
c
      write(24, 100) wmo24, wban24, ratp24, dsig1_24, 
     &   r_yy24, r_mo24, r_dd24, r_hh24, rmin24, rsec24,
     &   clat24, clon24, hbmsl24, heit24, dsig2_24,
     &   f_yy24, f_mo24, f_dd24, f_hh24, fmin24, fsec24,
     &   gpslat24, latmq24, latck24, gpslon24, lonmq24, lonck24, 
     &   gps_ht24, htmq24, htck24,
     &   uwnd24, uwmq24, uwck24, vwnd24, vwmq24, vwck24
 100  format(i5.5,1x,i5.5,1x,i2,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,f9.5,1x,f10.5,1x,i5,1x,i5,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,f9.5,1x,i2,1x,i2,1x,f10.5,1x,i2,1x,i2,
     &   1x,i5,1x,i2,1x,i2,
     &   1x,f6.1,1x,i2,1x,i2,1x,f6.1,1x,i2,1x,i2,1x,i3)
c
      RETURN                                                            
      END
C
C========================================================
C
      SUBROUTINE unpk_25(a25, tconv)                                    
      implicit none
      REAL kelvin
      PARAMETER (kelvin=273.15)
                                                                     
      integer wmo25, wban25, ratp25, dsig1_25, r_yy25, r_mo25,
     &   r_dd25, r_hh25, rmin25, hbmsl25, heit25, dsig2_25,
     &   f_yy25, f_mo25, f_dd25, f_hh25, fmin25, lvlsig25, flpc25,
     &   pr_25, sirc25, gpht25, hght25, wdir25 

       real rsec25, clat25, clon25, fsec25, rh_25, td_25, tdp25,
     &   wspd25
c
      common /msg_25/  wmo25, wban25, ratp25, dsig1_25, 
     &   r_yy25, r_mo25, r_dd25, r_hh25, rmin25, rsec25,
     &   clat25, clon25, hbmsl25, heit25, dsig2_25,
     &   f_yy25, f_mo25, f_dd25, f_hh25, fmin25, fsec25,
     &   lvlsig25, flpc25, pr_25, rh_25, sirc25,
     &   td_25, tdp25, gpht25, hght25, 
     &   wspd25, wdir25
c
      CHARACTER*1 tconv
      CHARACTER*8  CVAL,PMISS                                            
      EQUIVALENCE  (RVAL,CVAL)
      REAL*8       RVAL,BMISS
      REAL*8       a25(33)
      integer      lenout
c
      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
C
      character*100 of25
                                                                        
      DATA BMISS /   10E10  /                                                
      DATA PMISS /' MISSING'/                                            
                                                                        
C---------------------------------------------------------------------- 
C---------------------------------------------------------------------- 
C
      if (op25) then
        fname(17:26) = '_7Lvls.txt'
        of25 = outdir(1:lendir) // fname 
        open(25, file=of25, status='unknown')
c
        lenout = lendir + 26
        write(6, 10) of25(1:lenout)
 10     format(/'Opening O/P File:'
     &   /3x,a,'   (Standard & Sig Levels, low resolution)')
c
c  WRITE COLUMN HEADERS ...
c
        write(25, 25) stname
 25     format(
     &  'Message Type NC002025 -- RRS Standard & Sig. Levels, ',a
     &  //'  WMO  WBAN RT DS Year Mo Da Hr Mn   Sec      Lat ',
     &    '       Lon Bar_Ht    Ht DS Year Mo Da Hr Mn   Sec',
     &    ' LS FLPC  Press    RH SC    Td    DP  GPHT  HGHT   WSpd  WD')
c
        op25 = .false.
      endif
C
      wmo25 = 99999
      wban25 = 99999
      ratp25 = -9
      dsig1_25 = -9
      r_yy25 = 9999
      r_mo25 = 99 
      r_dd25 = 99
      r_hh25 = 99
      rmin25 = 99
      rsec25 = 99.     
      clat25 = -99.     
      clon25 = -999.     
      hbmsl25 = 99999
      heit25 = 99999
      dsig2_25 = -9
      f_yy25 = 9999
      f_mo25 = 99
      f_dd25 = 99
      f_hh25 = 99
      fmin25 = 99
      fsec25 = 99.     
      lvlsig25 = -9
      flpc25 = 999
      pr_25 = 999999
      rh_25 = -99.     
      sirc25 = -9
      td_25 = 999.     
      tdp25 = 999.     
      gpht25 = 99999
      hght25 = 99999
      wspd25 = 9999.     
      wdir25 = 999
c
c       WMO Block & Station No.
      if (a25(1) .lt. bmiss .and. a25(2) .lt. bmiss) then
       wmo25 = int(a25(1)*1000) + int(a25(2))
      endif
c
c       WBAN No.
      if (a25(3) .lt. bmiss) wban25 = int(a25(3))
c
c       Radiosonde Type
      if (a25(4) .lt. bmiss) ratp25 = int(a25(4))
c
c       Data Significance
      if (a25(5) .lt. bmiss) dsig1_25 = int(a25(5))
c
c       Balloon Release Year, mon, day, hr, min, sec
      if (a25(6) .lt. bmiss) r_yy25 = int(a25(6))
      if (a25(7) .lt. bmiss) r_mo25 = int(a25(7))
      if (a25(8) .lt. bmiss) r_dd25 = int(a25(8))
      if (a25(9) .lt. bmiss) r_hh25 = int(a25(9))
      if (a25(10) .lt. bmiss) rmin25 = int(a25(10))
      if (a25(11) .lt. bmiss) rsec25 = a25(11)
c
c       Latitude / Longitude
      if (a25(12) .lt. bmiss) clat25 = a25(12)
      if (a25(13) .lt. bmiss) clon25 = a25(13)
c
c       Ht Barometer Above Mean Sea Lvl
c       Height
      if (a25(14) .lt. bmiss) hbmsl25 = int(a25(14))
      if (a25(15) .lt. bmiss) heit25 = int(a25(15))
c
c       Data Significance
      if (a25(16) .lt. bmiss) dsig2_25 = int(a25(16))
c
c       Flight Level Year, mon, day, hr, min, sec
      if (a25(17) .lt. bmiss) f_yy25 = int(a25(17))
      if (a25(18) .lt. bmiss) f_mo25 = int(a25(18))
      if (a25(19) .lt. bmiss) f_dd25 = int(a25(19))
      if (a25(20) .lt. bmiss) f_hh25 = int(a25(20))
      if (a25(21) .lt. bmiss) fmin25 = int(a25(21))
      if (a25(22) .lt. bmiss) fsec25 = a25(22)
c
c       Level Significance
      if (a25(23) .lt. bmiss) lvlsig25 = int(a25(23))
c
c       Flt level Pressure Corr.
      if (a25(24) .lt. bmiss) flpc25 = int(a25(24))
c
c       Pressure 
      if (a25(25) .lt. bmiss) pr_25 = int(a25(25))
c
c       Relative Humidity
      if (a25(26) .lt. bmiss) rh_25 = int(a25(26))
c
c       Solar & Infrared Rad. Corr.
      if (a25(27) .lt. bmiss) sirc25 = int(a25(27))
c
c       Temperature                
      if (a25(28) .lt. bmiss) then
        if (tconv .eq. 'K') then
           td_25 = a25(28)
        else
           td_25 = a25(28) - kelvin
        endif
      endif
c
c       Dew Pt Temperature                
      if (a25(29) .lt. bmiss) then
        if (tconv .eq. 'K') then
           tdp25 = a25(29)
        else
           tdp25 = a25(29) - kelvin
        endif
      endif
c
c       Geopotential Ht.                       
      if (a25(30) .lt. bmiss) gpht25 = int(a25(30))
c
c       Height                    
      if (a25(31) .lt. bmiss) hght25 = int(a25(31))
c
c       Wind Speed                
      if (a25(32) .lt. bmiss) wspd25 = a25(32)
c
c       Height                    
      if (a25(33) .lt. bmiss) wdir25 = int(a25(33))
c
      write(25, 100) wmo25, wban25, ratp25, dsig1_25, 
     &   r_yy25, r_mo25, r_dd25, r_hh25, rmin25, rsec25,
     &   clat25, clon25, hbmsl25, heit25, dsig2_25,
     &   f_yy25, f_mo25, f_dd25, f_hh25, fmin25, fsec25,
     &   lvlsig25, flpc25, pr_25, rh_25, sirc25,
     &   td_25, tdp25, gpht25, hght25, 
     &   wspd25, wdir25
 100  format(i5.5,1x,i5.5,1x,i2,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,f9.5,1x,f10.5,1x,i5,1x,i5,1x,i2,
     &   1x,i4.4,4(1x,i2),1x,f5.2,
     &   1x,i2,1x,i4,1x,i6,1x,f5.1,1x,i2,
     &   1x,f5.1,1x,f5.1,1x,i5,1x,i5,
     &   1x,f6.1,1x,i3)
c
      RETURN                                                            
      END                                                               
c
c======================================================
c
      SUBROUTINE getnam(iwban)
c
c   STATION NAME TABLE:
c     1 - 4  Site ID,
c     6 -10  WBAN 
c    12 -16  WMO
c    18 -50  Location
c
      implicit none
c
      integer maxnam
      PARAMETER (maxnam = 92)
      integer iwban,i
      character*5 wban
      logical doloop

      common /fninfo/ lendir, op19, op20, op21, op22, op23, op24,
     &  op25, fname, outdir, stname
      character fname*28, outdir*80, stname*32
      integer lendir
      logical op19, op20, op21, op22, op23, op24, op25
c
      character*50 stnnam(maxnam)
c
      data stnnam /
     &  'kepz 03020 72364 Santa Teresa/El Paso, NM',
     &  'kdra 03160 72387 Desert Rock, NV',
     &  'knkx 03190 72293 San Diego, CA',
     &  'krev 03198 72489 Reno, NV',
     &  'klch 03937 72240 Lake Charles, LA',
     &  'kjan 03940 72235 Jackson, MS',
     &  'koun 03948 72357 Norman, OK',
     &  'klzk 03952 72340 Little Rock, AR',
     &  'kfwd 03990 72249 Fort Worth, TX',
     &  'ktfx 04102 72776 Great Falls, MT',
     &  'klkn 04105 72582 Elko, NV',
     &  'kotx 04106 72786 Spokane, WA',
     &  'kdtx 04830 72632 Detroit/White Lake, MI',
     &  'kilx 04833 74560 Lincoln, IL',
     &  'kapx 04837 72634 Gaylord, MI',
     &  'tjsj 11641 78526 San Juan, PR',
     &  'ktbw 12842 72210 Tampa Bay, FL',
     &  'keyw 12850 72201 Key West, FL',
     &  'kbro 12919 72250 Brownsville, TX',
     &  'kcrp 12924 72251 Corpus Christi, TX',
     &  'kgso 13723 72317 Greensboro, NC',
     &  'kiln 13841 72426 Wilmington(Cincinnati), OH',
     &  'kchs 13880 72208 Charleston, SC',
     &  'kjax 13889 72206 Jacksonville, FL',
     &  'kohx 13897 72327 Old Hickory/Nashville, TN',
     &  'kshv 13957 72248 Shreveport, LA',
     &  'kddc 13985 72451 Dodge City, KS',
     &  'ksgf 13995 72440 Springfield, MO',
     &  'ktop 13996 72456 Topeka, KS',
     &  'kcar 14607 72712 Caribou, ME',
     &  'kchh 14684 74494 Chatham, MA',
     &  'kbuf 14733 72528 Buffalo, NY',
     &  'kgrb 14898 72645 Green Bay, WI',
     &  'kinl 14918 72747 Intl Falls, MN',
     &  'kabr 14929 72659 Aberdeen, SD',
     &  'phto 21504 91285 Hilo, HI',
     &  'kdrt 22010 72261 Del Rio, TX',
     &  'phli 22536 91165 Lihue, HI',
     &  'kmaf 23023 72265 Midland, TX',
     &  'kama 23047 72363 Amarillo, TX',
     &  'kabq 23050 72365 Albuquerque, NM',
     &  'kdnr 23062 72469 Denver, CO',
     &  'kgjt 23066 72476 Grand Junction, CO',
     &  'ktus 23160 72274 Tucson, AZ',
     &  'koak 23230 72493 Oakland, CA',
     &  'kbis 24011 72764 Bismarck, ND',
     &  'klbf 24023 72562 North Platte, NE',
     &  'kriw 24061 72672 Riverton, WY',
     &  'kslc 24127 72572 Salt Lake City, UT',
     &  'kboi 24131 72681 Boise, ID',
     &  'kmfr 24225 72597 Medford, OR',
     &  'ksle 24232 72694 Salem, OR',
     &  'pant 25308 70398 Annette, AK',
     &  'paya 25339 70361 Yakutat, AK',
     &  'padq 25501 70350 Kodiak, AK',
     &  'pakn 25503 70326 King Salmon, AK',
     &  'pacd 25624 70316 Cold Bay, AK',
     &  'pasn 25713 70308 St. Paul Island, AK',
     &  'pafc 26409 70273 Anchorage, AK',
     &  'pafa 26411 70261 Fairbanks, AK',
     &  'pamc 26510 70231 Mcgrath, AK',
     &  'pabe 26615 70219 Bethel, AK',
     &  'paot 26616 70133 Kotzebue, AK',
     &  'paom 26617 70200 Nome, AK',
     &  'pabr 27502 70026 Barrow, AK',
     &  'ptya 40308 91413 Yap, WCI',
     &  'ptkr 40309 91408 Koror, Palau WCI',
     &  'pttp 40504 91348 Ponape, ECI',
     &  'ptkk 40505 91334 Chuuk (Truk), ECI',
     &  'pkmr 40710 91376 Majuro',
     &  'pgum 41406 91212 Agana, Guam',
     &  'kfgz 53103 72376 Flagstaff, AZ',
     &  'klix 53813 72233 Slidell, LA',
     &  'kffc 53819 72215 Peachtree City, GA',
     &  'kbmx 53823 72230 Birmingham, AL',
     &  'krnk 53829 72318 Blacksburg, VA',
     &  'kgyx 54762 74389 Gray (Portland), ME',
     &  'kaly 54775 72518 Albany, NY',
     &  'nstu 61705 91765 Pago Pago',
     &  'kmfl 92803 72202 Miami, FL',
     &  'klwx 93734 72403 Sterling, VA',
     &  'kwal 93739 72402 Wallops Island, VA',
     &  'kmhx 93768 72305 Newport, NC',
     &  'ktae 93805 72214 Tallahassee, FL',
     &  'kggw 94008 72768 Glasgow, MT',
     &  'kunr 94043 72662 Rapid City, SD',
     &  'kuil 94240 72797 Quillayute, WA',
     &  'kokx 94703 72501 Upton (Brookhaven), NY',
     &  'kpbz 94823 72520 Pittsburgh, PA',
     &  'koax 94980 72558 Omaha/Valley, NE',
     &  'kdvn 94982 74455 Quad Cities, IA',
     &  'kmpx 94983 72649 Chanhassen/Minneapolis, MN'/
c
      write(wban,'(i5.5)') iwban
c
      stname = 'Name Not In Table'
c
      doloop = .true.
      i = 0
      do while (doloop .and. i .lt. maxnam)
       i = i + 1
       if (wban .eq. stnnam(i)(6:10)) then
        doloop = .false.
        stname = stnnam(i)(18:49)
       endif
      enddo
c
      return
      end
c
c======================================================
c
 
