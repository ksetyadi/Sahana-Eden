function alertmessage2()
{
	$(document).ready(function()
		{
			 $("#message1").hide();
			 $("#message2").addClass("confirmation");
		 	 $("#message2"). show("slow");
		});
}


function view2(grid_data,column_model,rows,columns)
{
 	alertmessage2();   
    var selmod=new Ext.grid.CheckboxSelectionModel({singleSelect:true,header: 'Select header row'});
    var grid2=new Ext.grid.GridPanel({
            title: 'Edit \u2794 <u>Select header row</u> \u2794 Select table \u2794 Map columns to fields',
            renderTo: 'spreadsheet',
            height: 300,
            width: 'auto',
            store: grid_data,
            columns: column_model,
            frame: true,
            stripeRows: true,
            columnLines: true,
            sm: selmod,
            buttons :[
                    {
                        text: 'Back',
                        handler: function(){maker(json);grid2.hide();}
                    },
                    {
                        text: 'Next',
                        handler: function()
                        {
                            /*for(var i=0;i<grid_data.getCount();i++)
                                if(selmod.isIdSelected(i+''))
                                    Ext.Msg.alert("","Row number " + i + " selected");
                            */
			    var columns=0;
                            //Can use this bit later to extract cells from grid
                            grid_data.each(function(){
                                            str=this.fields.items;
					    
                                            for(k in str)
					    {	columns+=1;
					    }
						return false;
                            		
			      		    });
			    if(!selmod.getSelected())
				    Ext.Msg.alert("Error","Select column header row");
			    else
			    {grid2.hide();view3(selmod.getSelected(),columns-1,grid_data);}
                        }
                     }
                    ],
            buttonAlign: 'center'});
            grid2.render();

    
}
