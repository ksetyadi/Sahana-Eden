﻿Controls to add (point/line/polygon) on map but not to create feature in db
- to be used to locate a single feature from another module.

    <div id='gis_map_toolbar' >
        <fieldset id='gis_map_toolbar_fieldset' style="border: 1px solid ; padding: 5px; padding-bottom:2px;">

            <div id="gis_map_toolbar_default">
                <span title="<?= _t('Expand Map') ?>"><a onclick="shn_gis_map_expand()" alt="<?= _t('Full screen map')?>"><div id="gis_map_icon_expand" style="width: 24px; height: 22px;"></div></a></span>
            </div>
            <div id="gis_map_toolbar_manipulate">
                <span title="<?= _t('Navigate') ?>"><a onclick="shn_gis_map_control_navigate()" alt="<?= _t('Navigate')?>"><div id="gis_map_icon_select" style="width: 24px; height: 22px;"></div></a></span>
                <span title="<?= _t('Add Point')?>"><a onclick="shn_gis_map_control_add_point()" alt="<?= _t('Add Point')?>"><div id="gis_map_icon_addpoint" style="width: 24px; height: 22px;"></div></a></span>
                <span title="<?= _t('Add Line')?>"><a onclick="shn_gis_map_control_add_line()" alt="<?= _t('Add Line')?>"><div id="gis_map_icon_addline" style="width: 24px; height: 22px;"></div></a></span>
                <span title="<?= _t('Add Area')?>"><a onclick="shn_gis_map_control_add_polygon()" alt="<?= _t('Add Area')?>"><div id="gis_map_icon_addpolygon" style="width: 24px; height: 22px;"></div></a></span>
                <span title="<?= _t('Toggle Freehand Draw')?>"><a onclick="shn_gis_map_control_freehand()" alt="<?= _t('Toggle Freehand Draw')?>"><div id="gis_map_icon_freehand" style="width: 24px; height: 22px;"></div></a></span>
                <span title="<?= _t('Mode Description')?>" id="gis_map_icon_descripion"></span>
            </div>
        </fieldset>
    </div>

    ol_layers_features();    
    
    ol_add_feature('Feature', $icon);

function addControlsAddFeature(map) {
    // Add control to add new Points to the map
    pointControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Point);
    pointControl.featureAdded = shn_gis_map_add_geometry;
    map.addControl(pointControl);
    // Add control to add new Lines to the map
    lineControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Path);
    lineControl.featureAdded = shn_gis_map_add_geometry;
    map.addControl(lineControl);
    // Add control to add new Polygons to the map
    polygonControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Polygon);
    polygonControl.featureAdded = shn_gis_map_add_geometry;
    map.addControl(polygonControl);
    // Start with navigate activated
    shn_gis_map_control_navigate();
}

function shn_gis_map_add_geometry(feature){
    var fcopy = feature.clone();
    // need for later.
    var fcopygeom = fcopy.geometry.clone();
    var lonlat = fcopy.geometry.getBounds().getCenterLonLat();
    var proj_current = map.getProjectionObject();
    lonlat.transform(proj_current, proj4326);
    var lon_new = lonlat.lon;
    var lat_new = lonlat.lat;
    var wkt_new = fcopy.geometry.transform(proj_current, proj4326).toString();
    var type_new = featureTypeStr(fcopy);
    
    // Update form fields
    var x_gps = document.getElementById("gps_x");
    var y_gps = document.getElementById("gps_y");
    if( x_gps != null && y_gps != null){
        x_gps.value = lon_new;
        y_gps.value = lat_new;
    }

    // store x,y coords in hidden variables named loc_x, loc_y
    // must be set via calling page
    var x_point = document.getElementsByName("loc_x");
    var y_point = document.getElementsByName("loc_y");
    if(x_point != null && y_point != null){
        x_point[0].value = lon_new;
        y_point[0].value = lat_new;
    }
    // store type
    var loc_type = document.getElementsByName("loc_type");
    if(loc_type != null){
        loc_type[0].value = type_new;
    }
    // store wkt value
    var wkt_point = document.getElementsByName("loc_wkt");
    if(wkt_point != null){
        wkt_point[0].value = wkt_new;
    }
    
    // Remove last plot from layer
    featuresLayer.destroyFeatures(featuresLayer.features);
    
    // Add icon.  
    add_Feature(featuresLayer, 'newFeature', fcopygeom, '<?= $icon ?>');
}


// Add marker to map
function add_Feature(layer, feature_id, geom, iconURL){
    // Set icon dims
    var icon_img = new Image();
    icon_img.src = iconURL;
    var max_w = 25;
    var max_h = 35;
    var width = icon_img.width;
    var height = icon_img.height;
    if(width > max_w){
        height = ((max_w / width) * height);
        width = max_w;
    }
    if(height > max_h){
        width = ((max_h / height) * width);
        height = max_h;
    }
    // http://www.nabble.com/Markers-vs-Features--td16497389.html
    var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
    //style_mark.pointRadius = 12;
    style_marker.graphicWidth = width;
    style_marker.graphicHeight = height;
    style_marker.graphicXOffset = -(width / 2);
    style_marker.graphicYOffset = -height;
    style_marker.externalGraphic = iconURL;
    style_marker.graphicOpacity = 1;
    // Create Feature Vector + Props
    var featureVec = new OpenLayers.Feature.Vector(geom, null, style_marker);
    featureVec.fid = feature_id;
    // Add Feature.
    layer.addFeatures([featureVec]);
}
