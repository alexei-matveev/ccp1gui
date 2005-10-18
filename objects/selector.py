import exceptions 
import string
import pickle
import copy
import sys
import re

import Pmw
import Tkinter

class Selector( Pmw.MegaToplevel ):
    """A Pmw Widget containing a scene selector widget

       The lines in the text widget that make up the drag and drop widget are tagged with
       a tag that is the string representation of the vis id 

       Data structures:
       self.show_list is a list of vis that will make up the movie
       self.noshow_list is a list of vis that are excluded from the movie
       self.show_selected: a list that indicates which of the vis to be shown are seleced,
                           each item is a list of length 2, the first item of which is the tag
                           and the second a flag indicating if that line is selected or not

       self.noshow_selected: as above for items that wont' be shown
       

       There was a problem implementing dragndrop in that, when the mouse is clicked
       and held within a particular tag, if the mouse is then moved and released in
       a different tag, the tagname that is passed to the release event is the tagname
       of the tag that the mouse was originally clicked in, not the tagname of the tag
       that it was released in. For this reason I have had to implement a dictionary to
       track the line numbers of each tag and then look up the tag from the dictionary.
    """
    
                         
    def __init__( self, root, graph,  **kw ):

        self.debug = None
        
        self.root = root

        if not __name__ == '__main__':
            self.graph = graph
            self.balloon = graph.balloon
            self.error = graph.error
        else:
            self.balloon = Balloon()

        self.show_list = [] # List of the objects making up the animation in scene order
        self.noshow_list = [] # List of the objects excluded from the animation
        self.show_selected = [] # List of tuples ordered by the order of the tags in the animation
                                # The tuples are ( tag , selected ) where selected indicates
                                # if the tag is selected or not
        self.noshow_selected = [] # As above but for non-selected tags
        self.vis_to_name = {}
        self.line_to_tag = {}     # line_to_tag maps line ->  tag on that line
        self.tag_to_type = {}     # tag_to_type maps tag ->  whether the vis tagged with this
                                  # tag is being shown or not
        self.tag_to_vis = {}      # map tags to the vis object
        
        self.initialtag = None # For tracking which tag the mouse click event happen in
        self.shifton = None # For tracking if the shift key is pressed

        # The variables dictating how the text widget is displayed:
        self.name_width = 50
        self.pad_width = 5
        self.num_width = 5
        self.select_colour = "gray"
        self.standardfg = "black"
        self.standardbg = "white"
        self.headerfg = "white"
        self.headerbg = "black"

        if __name__ == '__main__':
            # Set up some dummy objects for when we are debugging.
            self.objlist = []
            self.setup_debug()

        mytitle="Image Selector Widget"
        Pmw.MegaToplevel.__init__( self, self.root, title=mytitle )
        
        self.build()
        self.refresh()

    def build(self):
        """ The Widget is split into three parts:
            A text widget to display images to show together with those to ignore
             - the text widget is split into two sections separated by a header line,
             with the top section listing the images to show and the bottom those
             that are to be ignored.
            A frame below the text widget hold three buttons to add or remove images
            from the animation or display the image that is selected.
            A bottom frame holding three buttons to Refresh the widget and quit with or
            without saving.
        """
        self.show_list_widget = Pmw.ScrolledText( self.interior(),
                                                   text_background = "white"
                                                      )
        # Alias the text widget so we can access it easier
        self.scene_text = self.show_list_widget.component( 'text' )
        
        # need to bind these tags here for reason mentioned in class description
        self.scene_text.bind( "<ButtonRelease-1>", self.buttonrelease1 )
        self.scene_text.bind( "<B1-Motion>", self.b1_motion )
        self.scene_text.bind( "<Double-Button-1>", self.double_button1 )
        #self.scene_text.bind( "<Shift_L>", self.shift_pressed )
        #self.scene_text.bind( "<Return>", self.shift_pressed )
        self.bind( "<KeyPress>", self.key_pressed )
        self.bind( "<KeyRelease>", self.key_released )
        
        self.show_list_widget.pack(fill='both', expand=1)

        # The buttons to add, remove and display images
        self.scene_control_frame = Tkinter.Frame( self.interior() )
        self.scene_control_frame.pack()
        self.add_button = Tkinter.Button( self.scene_control_frame, text='Add', command=self.__addclicked )
        self.balloon.bind( self.add_button, 'Add image(s) to the animation.' )
        
        self.remove_button = Tkinter.Button( self.scene_control_frame, text='Remove', command=self.__removeclicked )
        self.balloon.bind( self.remove_button, 'Remove image(s) from the animation.' )
        self.display_button = Tkinter.Button( self.scene_control_frame, text='Display Image',
                                              command=self.__displayclicked )
        self.balloon.bind( self.display_button, 'Display a selected image' )
        self.add_button.pack( side='left' )
        self.remove_button.pack( side='left' )
        self.display_button.pack( side='left' )

        # The buttons to Refresh, and Quit
        self.bottom_frame = Tkinter.Frame( self.interior() )
        self.bottom_frame.pack()
        self.refresh_button = Tkinter.Button( self.bottom_frame,
                                              text='Clear and Refresh',
                                              command=self.__refreshclicked )
        self.balloon.bind( self.refresh_button, 'Generate a fresh list of available images' )
        self.quit_nosave_button = Tkinter.Button( self.bottom_frame,
                                                  text='Quit without Save',
                                                  command = lambda s=self: s.quit( save=None ) )
        self.balloon.bind( self.quit_nosave_button, 'Quit: Do not use this list of animations' )
        self.quit_save_button = Tkinter.Button( self.bottom_frame,
                                              text='Save and Quit',
                                              command=lambda s=self :s.quit( save = 1 ) )
        self.balloon.bind( self.quit_save_button, 'Quit: Use selected list of animations' )
        self.refresh_button.pack( side='left' )
        self.quit_nosave_button.pack( side='left' )
        self.quit_save_button.pack( side='left' )
        

    def __addclicked(self):
        """ The add button was clicked so add the items at the end of the show_list
        """
        endindex = len( self.show_list ) + 1
        self.add_to_animation( endindex  )

    def __removeclicked(self):
        """ The remove button was clicked so remove all selected items from the list
        """
        self.remove_from_animation()

    def __displayclicked(self):
        """ The display button was clicked so display the selected image(s)
        """

        if self.debug:
            print "DEBUG: __display_clicked"
            print "DEBUG: self.show_selected: ", self.show_selected
            print "DEBUG: self.noshow_selected: ", self.noshow_selected

        # Hide all the images
        for vis in self.show_list:
            vis.Hide()
        for vis in self.noshow_list:
            vis.Hide()

        # Show all the show images that have been selected
        for tag, selected in self.show_selected:
            if selected :
                for vis in self.show_list:
                    if str( id(vis) ) == tag:
                        vis.Show()
        
        # Show all the noshow images that have been selected
        for tag, selected in self.noshow_selected:
            if selected :
                for vis in self.noshow_list:
                    if str( id(vis) ) == tag:
                        vis.Show()


    def __refreshclicked( self ):
        """ Clear and reresh was clicked so generate a new list of objects form the GUI.
        """
        self.refresh()
        
    def quit( self, save = None ):
        """ Quit was clicked so hide the scence widget and pass back the show_list
            if the user clicked save
        """
        if save :
            print "Quitting Scene Widget and saving"
            # Hide all the images
            for vis in self.show_list:
                vis.Hide()
            for vis in self.noshow_list:
                vis.Hide()
            self.graph.ani_list = self.show_list
            # Reset the frame number for playing images
            self.graph.frame_no = 0
            self.graph._ani_show()
            
        #print "Leaving scene with self.ani_list = ",self.graph.ani_list
        self.withdraw()
        
    def refresh(self):
        """ Regenerate new show and noshow lists from graph.data_list (see main.py)
            Destroy all the tags that were applied to the text as these are regenerated
            by the draw method.
        """

        # Clear the vis lists
        #self.vis_list = []
        self.show_list = []
        self.noshow_list = []
        self.vis_to_name = {}

        # Clear the slected list
        # self.show_selected = []
        # self.noshow_selected = []
        # ABOVE IS ACTUALLY DONE IN redraw
        
        # Delete all tags
        for tag in self.scene_text.tag_names():
            self.scene_text.tag_delete( tag )
        
        if __name__ == '__main__':
            for vis in self.objlist:
                if vis.IsShowing():
                    self.show_list.append( vis )
                else:
                    self.noshow_list.append( vis )
                name = vis.name
                self.vis_to_name[ vis ] = name
                
        else:
            #Grab the objects to be visualised from the data_list
            for obj in self.graph.data_list:
                t = id(obj)
                try:
                    visl = self.graph.vis_dict[t]
                    for vis in visl:
                        # Work out a name
                        try:
                            name = vis.title
                        except:
                            if obj.name is not None:
                                name = obj.name
                            else:
                                name = obj.title
                        self.vis_to_name[ vis ] = name

                        #if vis.IsShowing():
                        #    self.show_list.append( vis )
                        #else:
                        #    self.noshow_list.append( vis )
                        self.show_list.append( vis )
                        
                except KeyError:
                    pass
        self.redraw()
            

    def redraw(self):
        """ Clear and then redraw the text widget to display the images we are showing based on
            show_list and noshow_list.
            We create the format string for writing out the tags based on the
            the variables self.name_width, pad_width, num_width, select_colour etc. defined in init
            It is also at this point that we add the entires to tag_to_type, line_to_tag and the
            entries in show and noshow_selected
        """

        # For the time being we clear out all selections and tags - we can consider being clever
        # and keeping selections between events later
        self.show_selected = []
        self.noshow_selected = []
        # just nuke all the tags
        for tag in self.scene_text.tag_names():
            self.scene_text.tag_delete( tag )

        # Enable the widget
        self.scene_text.configure( state = "normal" )
        
        # Delete all the text
        self.scene_text.delete( "0.0", "end" )
        self.scene_text.configure( foreground= self.standardfg, background=self.standardbg )

        # Add a header line for the images
        linestart = self.scene_text.index( "insert" )
        self.scene_text.insert( 'insert', "Selected Images\n" )
        lineend = self.scene_text.index( "insert" )
        tag = "show_header"
        self.scene_text.tag_add( tag, linestart, lineend )
        self.scene_text.tag_config( "show_header",
                                    background=self.headerbg,
                                    foreground=self.headerfg )

        # Add the tag header and the line it is on to the dictionary
        line = int (string.split( linestart, "." )[0])
        self.line_to_tag[ line ] = tag
        self.tag_to_type[ tag ] = "show"
                
        # Fill the text widget with the list of images we are showing
        count = 0
        for vis in self.show_list:
            name = self.vis_to_name[ vis ]
            t = id(vis)
            #name = str(t )

            # Write out the name in name_width chars
            linestart = self.scene_text.index( "insert" ) 
            formatstr= '%-'+ str( self.name_width ) +'s'
            namestr = formatstr % name
            self.scene_text.insert('insert',namestr )

            # create a pad of self.pad_width blank characters
            formatstr= '%-'+ str( self.pad_width ) +'s'
            padstr = formatstr % ''
            self.scene_text.insert('insert',padstr )

            # Write the index in num_width field
            formatstr= '%-'+ str( self.num_width ) +'s'
            numstr = formatstr % str(count)
            self.scene_text.insert('insert',numstr )

            # Get the index of EOL
            lineend = self.scene_text.index( "insert" )

            # Create a tag for the whole line using the id of the obj as the tag
            tag = str(t)
            self.scene_text.tag_add( tag, linestart, lineend )
            # Add the tag and the line it is on to the dictionaries
            line = int (string.split( linestart, "." )[0])
            self.line_to_tag[ line ] = tag
            self.tag_to_type[ tag ] = "show"
            self.tag_to_vis[ tag ] = vis
            self.show_selected.append( [ tag, None ] )
            
            # Bind the tags to events:
            self.scene_text.tag_bind( tag, "<ButtonPress-1>",
                                       lambda event, tn=tag : self.tag_buttonpress1( event, tn )  ) 
           
            # Move to the next line
            self.scene_text.insert('insert','\n' )
            
            count += 1

        # Add a line seperating show from noshows
        linestart = self.scene_text.index( "insert" )
        self.scene_text.insert( 'insert', "Rejected Images\n" )
        lineend = self.scene_text.index( "insert" )
        tag = "noshow_header"
        self.scene_text.tag_add( tag, linestart, lineend )
        self.scene_text.tag_config( "noshow_header",
                                    background=self.headerbg,
                                    foreground=self.headerfg )
        line = int (string.split( linestart, "." )[0])
        self.line_to_tag[ line ] = tag
        self.tag_to_type[ tag ] = "noshow"
        
        # Fill the rest of the text widget with the list of images we are not showing
        for vis in self.noshow_list:
            name = self.vis_to_name[ vis ]
            t = id(vis)
            #name = str( t )
            
            linestart = self.scene_text.index( "insert" )
            width = int ( self.name_width ) + int( self.pad_width ) + int( self.num_width )
            formatstr= '%-'+ str( width ) +'s'
            namestr = formatstr % name
            self.scene_text.insert('insert',namestr )
            lineend = self.scene_text.index( "insert" )
            # Create a tag for the whole line starting with noshow so know this
            # is a tag for an vis we are not showing
            tag = str(t)
            self.scene_text.tag_add( tag, linestart, lineend )
            
            # Add the tag and the line it is on to the dictionaries
            line = int (string.split( linestart, "." )[0])
            self.line_to_tag[ line ] = tag
            self.tag_to_type[ tag ] = "noshow"
            self.tag_to_vis[ tag ] = vis
            self.noshow_selected.append( [ tag, None ] )

            # Bind the tags to events:
            self.scene_text.tag_bind( tag, "<ButtonPress-1>",
                                       lambda event, tn=tag : self.tag_buttonpress1( event, tn )  )
            
            # Move to the next line
            self.scene_text.insert('insert','\n' )

        #self.scene_text.configure( state = "disabled" )
        
    def tag_buttonpress1(self, event, tag):
        """ A tag has been clicked on - set the initialtag flag so that
            on release we can check whether the release event came from
            the same or a different tag.
        """
        if (self.debug):
            print "DEBUG: tag_button1press: tag %s was clicked on" % tag

        self.initialtag = tag

        return 'break'
            

    def key_pressed( self, event ):
        """  A key was pressed - check if it was the shift key and set shifton if so
        """

        if event.keysym == "Shift_L":
            self.shifton = 1

        if self.debug:
            print "DEBUG: key %s was pressed" % event.keysym

        return 'break'

    def key_released( self, event ):
        """  A key was released: if it was the shift key, unset shifton
        """
        if event.keysym == "Shift_L":
            self.shifton = None

        if self.debug:
            print "DEBUG: key %s was released" % event.keysym

        return 'break'

    def b1_motion( self, event ):
        """ Moving whilst holding down mouse button 1 so change cursor to exchange
        """

        if not event.widget.cget( "cursor" ) == "exchange":
            event.widget.config( cursor = "exchange" )
        else:
            pass

        # We need to return break here to disable all higher level bindings in tk.
        # otherwise moving the mouse with the left button held down causes all text
        # between the click event and the pointer to be highlighed - see:
        # "http://effbot.org/zone/tkinter-events-and-bindings.htm"
        return 'break'

    def buttonrelease1( self, event ):
        """ The mouse button has been released.
            Change the cursor back to default
            Work out if the release even happend in the same or a different tag to the press event
            Call dragged_to_show or noshow depending on the tag we are on
        """
        # Change the mouse back to default cursor
        if event.widget.cget( "cursor" ) == "exchange":
            event.widget.config( cursor = "" )
        else:
            pass

        # Get the line number the mouse is on 
        current = event.widget.index("current")
        linenum = int( string.split( current, "." )[0] )

        if self.debug:
            print "DEBUG: in buttonrelease1"
        
        # Find out in which tag the release happend in (from line number )
        try:
            tag = self.line_to_tag[ linenum ]
            if (self.debug):
                print "DEBUG: tag in buttonrelease1 is %s" % tag
                print "DEBUG: self.shifton is %s" % self.shifton
            
            if tag == self.initialtag:
                # Button released in the same tag
                # If the shift key is down we are (de-)selecting
                # all tags between here and the next selected tag in the list
                if self.shifton:
                    self.shift_select( tag )
                else:
                    self.toggle_select_tag( tag )
            else:
                # Button released in different tag so we are dragging all selected tags to this spot
                tagtype = self.tag_to_type[ tag ]
                if ( tagtype == "show" ):
                    self.dragged_to_show_tag( tag )
                elif (  tagtype == "noshow" ):
                    self.dragged_to_noshow_tag()
        except KeyError, e:
            # The line number doesn't correspond to any tag in the dictionary
            # so we assume he user clicked in an empty field
            #print "User clicked on an unknown tag"
            pass

        return 'break'

    def toggle_select_tag( self,tag ):
        """
           A tag has been clicked on with the mouse.
           See if the tag is selected to determine if we are selecting or deselecting the tag.
        """
        if self.debug:
            print "DEBUG: toggle_select_tag tag %s" % tag

        got = self.is_selected( tagquery=tag )
        if got:
            self.deselect_tag( tag )
        else:
            self.select_tag( tag )
            
        if self.debug:
            print "DEBUG: show_selected leaving toggle_select_tag is ",self.show_selected
            print "DEBUG: noshow_selected leaving toggle_select_tag is ",self.noshow_selected

    def double_button1( self, event ):
        """Mouse was double-clicked so deselect all selections
        """
        if self.debug:
            print "DEBUG: double_button1: de-selecting all tags"
            

        for tag, select in self.show_selected:
            if self.is_selected( tagquery = tag):
                self.deselect_tag( tag )
                
        for tag, select in self.noshow_selected:
            if self.is_selected( tagquery = tag):
                self.deselect_tag( tag )
 
    def shift_select( self, selected_tag ):
        """ A tag was selected with the shift key pressed down.
            We determine the tag type to see which frame we are in and then
            determine the index of this tag and that of the selected tag that
            is furthest down the list of selected tags (if no tags are selected
            we just select this tag ). Otherwise, if the tag that has been clicked
            on is lower down the list of selected tag, we select all tags between the
            last selected tag and tag that was clicked on.
            If the tag that was clicked on is higher up the list than the lowest selected
            tag then we deselect all tags below the tag that was clicked on.

            NOTE: currently don't make any check if the last selection happened in the
                  same frame as this the shift-click event
           
        """

        if self.debug:
            print "DEBUG: in shift_select with tag %s " % selected_tag
            
        selected_type = self.tag_to_type[ selected_tag ]

        # Determine if any tags of this type have been selected and just select
        # the tag that's been clicked on if not
        got = self.is_selected( typequery = selected_type )
        if not got:
            self.select_tag( selected_tag )

        # We now know that at least one tag was selected so find out what type
        # and get the index of that tag in the selected list
        selected_index = self.get_index( selected_tag, selected_type )

        # Get the highest indexed selected tag of the type in question
        highest_index = self.get_highest_index( ttype = selected_type )

        if highest_index > selected_index :
            # We are deselecting all tags between highest_index back up to selected_index
            #NB:  We need to add 1 to highest_index to take into account the header line
            if selected_type == "show":
                for tag, select in self.show_selected[ selected_index : highest_index + 1 ]:
                    self.deselect_tag( tag )
            elif selected_type == "noshow":
                for tag, select in self.noshow_selected[ selected_index : highest_index + 1 ]:
                    self.deselect_tag( tag )
                
        elif highest_index < selected_index :
            # We are selecting all tags between highest_index back and selected_index
            #NB:  We need to add 1 to the indexs to take into account of the header lines
            if selected_type == "show":
                for tag, select in self.show_selected[ highest_index + 1 : selected_index + 1 ]:
                    self.select_tag( tag )
            elif selected_type == "noshow":
                for tag, select in self.noshow_selected[ highest_index + 1 : selected_index + 1 ]:
                    self.select_tag( tag )
        else:
            # Should never get here
            pass
            
            
    def dragged_to_show_tag( self, selectedtag ):
        """We were dragged to a show_tag so get the index of the tag in the show_list
           and then call add_to_animation with that index
        """
        got=0
        if ( selectedtag == "show_header" ) or ( selectedtag == "noshow_header" ):
            index = 0
        else:
            index=0
            for obj in self.show_list:
                if  str( id(obj) )  == selectedtag :
                    got = 1
                    break
                    # Found object so i is index in show_list
                else:
                    pass
                index += 1
            if got == 0 :
                print "Error in dragged_to_show_tag: obj not found in show_list"
                return

        if self.debug:
            print "DEBUG: in dragged_to_show tag with tag: %s index: %s " % ( selectedtag, index )
        
        self.add_to_animation( index )

    def dragged_to_noshow_tag( self ):
        """ We were dragged to a noshow
            Check if
        """
        self.remove_from_animation()
                
    def add_to_animation( self, index ):
        """
        We are adding images to list of those to be shown.
        
        In the cases where shown objects are involved we need to firstly remove
        these objects from the show_list. Then we calculate the index of the item
        that we are moving things onto in the revised show_list.
        
        Finally we loop through the shown objects and then the noshow objects inserting
        them into the show_list above the object that things were moved onto.
        """
        if self.debug:
            print "DEBUG: Adding to animation at index %s" % index
            print "DEBUG: self.ani_selected is ",self.show_selected
            print "DEBUG: self.noshow_selected is ",self.noshow_selected

        insertlist = []
        if self.is_selected( typequery = "show" ):
            #print "Adding objects from show selected to insertlist"
            
            # For shown objects remove them from the list and add to the list
            # of objects we will be inserting and deselect the tag
            for tag, selected in self.show_selected:
                if selected:
                    vis = self.tag_to_vis[ tag ]
                    insertlist.append( vis )
                    self.show_list.remove( vis )
                    self.deselect_tag( tag )
                    
        # Add any images from the noshow_selected to the insertlist
        if self.is_selected( typequery = "noshow" ):
            #print "Adding objects from noshow_selected to insertlist", self.noshow_selected
            for tag, selected in self.noshow_selected:
                if selected:
                    vis = self.tag_to_vis[ tag ]
                    insertlist.append( vis )
                    self.noshow_list.remove( vis )
                    self.deselect_tag( tag )

        if len( insertlist ) == 0:
            print "No items to insert in dragged to show list"
            return


        # Now we just insert the items from the insertlist into show_list
        # we increment the index so the items go in in the order they were
        # in the insertlist
        for obj in insertlist:
            self.show_list.insert( index, obj )
            index += 1
            
        # Now redraw the text widget
        self.redraw()
        
    def remove_from_animation( self ):
        """ The mouse was dragged onto a noshow tag.
            So move all selected tags in the show_list to the noshow list
            and then refresh the widget.
        """
        if self.debug:
            print "DEBUG: in remove_from_animation"
            print "DEBUG: show_selected is ",self.show_selected

        if self.is_selected( typequery = "show" ):
            for tag, selected in self.show_selected:
                if selected:
                    vis = self.tag_to_vis[ tag ]
                    self.noshow_list.append( vis )
                    self.show_list.remove( vis )

            self.redraw()
        else:
            print "dragged_to_noshowtag: No Shown items selected for removal!"

    def is_selected( self, tagquery=None, typequery=None ):
        """ Return 1 if any of the tags in the text widget are selected, None if not
            If the optional argument tag is suppled, it returns 1 if the tag is selected
            or None otherwise
            If the optional argument ttype is supplied we return 1 if any of the tags
            of the selected type are selected or None otherwise
        """

        if self.debug:
            print "DEBUG: Entering is_selected: tagquery: \"%s\" typequery: \"%s\"" %  ( tagquery, typequery )
            
        if tagquery:
            querytag = tagquery
            got_tag = None

        got_show = None
        for tag, selected in self.show_selected:
            #print "show_selected: showtag %s selected %s" % ( showtag, selected )
            if selected:
                got_show = 1
            if tagquery:
                if tag == querytag and selected:
                    got_tag = 1

        got_noshow = None
        for tag, selected in self.noshow_selected:
            #print "noshow_selected: noshowtag %s selected %s" % ( noshowtag, selected )
            if selected:
                got_noshow = 1
            if tagquery:
                if tag == querytag and selected:
                    got_tag = 1

        # Sort out the return value depending on how we were called
        if tagquery:
            retval = got_tag
        elif typequery:
            if typequery == "show":
                retval = got_show
            elif typequery == "noshow":
                retval = got_noshow
            else:
                print "Unknown typequery in is_selected: %s " % typequery
        else:
            if not got_show and not got_noshow:
                retval = None
            else:
                retval = 1
            
        if self.debug:
            print "DEBUG: self.is_selected returning %s" % retval

        return retval

    def get_index( self, itag, ttype ):
        """ Get the index of tag in the list of type ttype
        """
        if self.debug:
            print "DEBUG: Entering get_index - tag: %s ttype: %s " % ( itag, ttype )

        retval = None
        if ttype == "show":
            index = 0
            for tag, selected in self.show_selected:
                if tag == itag:
                    retval = index
                    break
                index += 1
                
        elif ttype == "noshow":
            index = 0
            for tag, selected in self.noshow_selected:
                if tag == itag:
                    retval = index
                    break
                index += 1

        else:
            print "ERROR!: get_index - unrecognised ttype!"

        if not retval:
            print "ERROR!: get_index tag %s not in ttype %s" % ( itag, ttype )
            
        if self.debug:
            print "DEBUG: get_index returning: %s" % retval

        return int( retval )
        
        

    def get_highest_index( self, ttype ):
        """ Return the highest index of the tag that is selected in either of
            show_selected or noshow_selected (determined by ttype).
        """

        if self.debug:
            print "DEBUG: Entering get_highest_index - ttype: %s " % ttype

        retval = None
        if ttype == "show":
            got_show = None
            index = 0
            for showtag, selected in self.show_selected:
                #print "show_selected: showtag %s selected %s" % ( showtag, selected )
                if selected:
                    got_show = index
                index += 1
            retval = got_show
                
        elif ttype == "noshow":
            got_noshow = None
            index = 0
            for noshowtag, selected in self.noshow_selected:
                #print "noshow_selected: noshowtag %s selected %s" % ( noshowtag, selected )
                if selected:
                    got_noshow = index
            retval = got_noshow
        else:
            print "get_highest_index - unrecognised ttype!"
            
        if self.debug:
            print "DEBUG: get_highest_index returning %s" % retval

        retval = int( retval )

        return retval


    def select_tag( self, tag ):
        """ 1. Set the flag in the relevant list
            2. Highlight the tag by configuring its fg & bg
        """
        
        ttype = self.tag_to_type[ tag ]

        if self.debug:
            print "DEBUG: Entering select_tag: tag is %s ttype is %s " % ( tag, ttype )
            print "DEBUG:          noshow_selected", self.noshow_selected
            print "DEBUG:          show_selected", self.show_selected

        if ttype == "show":
            index = 0
            for show, selected in self.show_selected:
                if show == tag:
                    if selected:
                        print "Selecting an already selected show tag!"
                    else:
                        self.show_selected[ index ][1] = 1
                index += 1

        elif ttype == "noshow":
            index = 0
            for noshow, selected in self.noshow_selected:
                if noshow == tag:
                    if selected:
                        print "Selecting an already selected noshow tag!"
                    else:
                        self.noshow_selected[ index ][1] = 1
                index += 1
        else:
            print "select_tag: unknown tag selected %s" % tag
            return
            
        self.scene_text.tag_config( tag,
                                    background=self.select_colour )

    def deselect_tag( self, tag ):
        """ 1. Set the flag in the relevant list
            2. Remove highlight by configuring tags fg & bg
        """

        if ( tag == "show_header" ) or ( tag == "noshow_header" ):
            return
        
        if self.debug:
            print "DEBUG: De-selecting tag: ",tag
            
        ttype = self.tag_to_type[ tag ]
        #print "deselecting tag, ttype is: %s" % ttype

        if ttype == "show":
            index = 0
            for show, selected in self.show_selected:
                if show == tag:
                    if not selected:
                        print "De-selecting an already deselected show tag!"
                    else:
                        self.show_selected[ index ][1] = None
                index += 1

        elif ttype == "noshow":
            index = 0
            for noshow, selected in self.noshow_selected:
                if noshow == tag:
                    if not selected:
                        print "De-selecting an already deselected noshow tag!"
                    else:
                        self.noshow_selected[ index ][1] = None
                index += 1
        else:
            print "deselect_tag: unknown tag selected %s" % tag
            return
            
        self.scene_text.tag_config( tag,
                                    background=self.standardbg )

    def setup_debug( self ):
        """ We are in debugging mode so set up some dummy data
        """
        one = visobj( show=1, name = 'one'  )
        two = visobj( show=1, name = 'two' )
        three = visobj( show=1, name = 'three' )
        four = visobj( show=0, name = 'four' )
        five = visobj( show=0, name = 'five' )
        six = visobj( show=1, name = 'six' )
        seven = visobj( show=0, name = 'seven' )
        eight = visobj( show=1, name = 'eight' )
        nine = visobj( show=1, name = 'nine' )
        ten = visobj( show=1, name = 'ten' )
        eleven = visobj( show=1, name = 'eleven' )

        self.objlist.append( one )
        self.objlist.append( two )
        self.objlist.append( three )
        self.objlist.append( four )
        self.objlist.append( five )
        self.objlist.append( six )
        self.objlist.append( seven )
        self.objlist.append( eight )
        self.objlist.append( nine )
        self.objlist.append( ten )
        self.objlist.append( eleven )

class Balloon:
    """ Dummy balloon for debugging purposes
    """

    #def __init__( self ):
    #    pass
    def bind( self, crap, othercrap):
        pass
    
class visobj:
    """ A dummy object that you can set a show attribute of
    """
    def __init__( self,show=None, name=None ):
        if show == 1:
            self.show = 1
        else:
            self.show = None

        if name:
            self.name = name
            
    def IsShowing(self):
        if self.show:
            return 1
        else:
            return None

    def _hide(self):
        self.show = None
        
    def Show(self):
        self.show = 1
        print "Object %s will be shown" % str( id( self ) )
        
 
if __name__ == '__main__':
    root = Tkinter.Tk()
    #root.withdraw()
    t = Selector(root, None )
    #t.withdraw()
    #Button(command = lambda: t.show(), text = 'show').pack()
    root.mainloop()
