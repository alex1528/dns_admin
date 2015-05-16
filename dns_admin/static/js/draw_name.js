function Topology(ele){
    typeof(ele)=='string' && (ele=document.getElementById(ele));
    var w=ele.clientWidth,
        h=ele.clientHeight,
        self=this;
    this.force = d3.layout.force().gravity(.05).distance(200).charge(-800).size([w, h]);
    this.nodes=this.force.nodes();
    this.links=this.force.links();
    this.clickFn=function(){};
    this.vis = d3.select(ele).append("svg:svg")
                 .attr("width", w).attr("height", h).attr("pointer-events", "all");

    this.force.on("tick", function(x) {
      self.vis.selectAll("g.node")
          .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

      self.vis.selectAll("line.link")
          .attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });
    });
}


Topology.prototype.doZoom=function(){
    d3.select(this).select('g').attr("transform","translate(" + d3.event.translate + ")"+ " scale(" + d3.event.scale + ")");

}


//增加节点
Topology.prototype.addNode=function(node){
    this.nodes.push(node);
}

Topology.prototype.addNodes=function(nodes){
    if (Object.prototype.toString.call(nodes)=='[object Array]' ){
        var self=this;
        nodes.forEach(function(node){
            self.addNode(node);
        });

    }
}

//增加连线
Topology.prototype.addLink=function(source,target){
    this.links.push({source:this.findNode(source),target:this.findNode(target)});
}

//增加多个连线
Topology.prototype.addLinks=function(links){
    if (Object.prototype.toString.call(links)=='[object Array]' ){
        var self=this;
        links.forEach(function(link){
            self.addLink(link['source'],link['target']);
        });
    }
}


//删除节点
Topology.prototype.removeNode=function(id){
    var i=0,
        n=this.findNode(id),
        links=this.links;
    while ( i < links.length){
        links[i]['source']==n || links[i]['target'] ==n ? links.splice(i,1) : ++i;
    }
    this.nodes.splice(this.findNodeIndex(id),1);
}

//删除节点下的子节点，同时清除link信息
Topology.prototype.removeChildNodes=function(id){
    var node=this.findNode(id),
        nodes=this.nodes;
        links=this.links,
        self=this;

    var linksToDelete=[],
        childNodes=[];
    
    links.forEach(function(link,index){
        link['source']==node 
            && linksToDelete.push(index) 
            && childNodes.push(link['target']);
    });

    linksToDelete.reverse().forEach(function(index){
        links.splice(index,1);
    });

    var remove=function(node){
        var length=links.length;
        for(var i=length-1;i>=0;i--){
            if (links[i]['source'] == node ){
               var target=links[i]['target'];
               links.splice(i,1);
               nodes.splice(self.findNodeIndex(node.id),1);
               remove(target);
               
            }
        }
    }

    childNodes.forEach(function(node){
        remove(node);
    });

    //清除没有连线的节点
    for(var i=nodes.length-1;i>=0;i--){
        var haveFoundNode=false;
        for(var j=0,l=links.length;j<l;j++){
            ( links[j]['source']==nodes[i] || links[j]['target']==nodes[i] ) && (haveFoundNode=true) 
        }
        !haveFoundNode && nodes.splice(i,1);
    }
}



//查找节点
Topology.prototype.findNode=function(id){
    var nodes=this.nodes;
    for (var i in nodes){
        if (nodes[i]['id']==id ) return nodes[i];
    }
    return null;
}


//查找节点所在索引号
Topology.prototype.findNodeIndex=function(id){
    var nodes=this.nodes;
    for (var i in nodes){
        if (nodes[i]['id']==id ) return i;
    }
    return -1;
}

//节点点击事件
Topology.prototype.setNodeClickFn=function(callback){
    this.clickFn=callback;
}

//更新拓扑图状态信息
Topology.prototype.update=function(){
  var link = this.vis.selectAll("line.link")
      .data(this.links, function(d) { return d.source.id + "-" + d.target.id; })
      .attr("class", function(d){
            return d['source']['status'] && d['target']['status'] ? 'link' :'link link_error';
      });

  link.enter().insert("svg:line", "g.node")
      .attr("class", function(d){
         return d['source']['status'] && d['target']['status'] ? 'link' :'link link_error';
      });

  link.exit().remove();

  var node = this.vis.selectAll("g.node")
      .data(this.nodes, function(d) {if (d.vm_tag != undefined){console.log(d.vm_tag)}; return d.id;});

  var nodeEnter = node.enter().append("svg:g")
      .attr("class", "node")
      .call(this.force.drag);

  //增加图片，可以根据需要来修改
  var self=this;
  nodeEnter.append("svg:image")
      .attr("class", "circle")
      .attr("xlink:href", function(d){
         //根据类型来使用图片
         return d.img
      })
      .attr("x", "-32px")
      .attr("y", "-32px")
      .attr("width", "64px")
      .attr("height", "64px")
      .on('click',function(d){ if (d.vm_tag != undefined){console.log(d.vm_tag)}; d.expand && self.clickFn(d);})

  nodeEnter.append("svg:text")
      .attr("class", "nodetext")
      .attr("dx", 15)
      .attr("dy", -35)
      .text(function(d) { if (d.vm_tag != undefined) {  return d.name + "(" + d.vm_tag + ")" } else { return d.name}});

  
  node.exit().remove();

  this.force.start();
}




function indexNode(container,nodes,links){
    var topology=new Topology(container);
    topology.addNodes(nodes);
    topology.addLinks(links);
    topology.setNodeClickFn(function(node){
        if(!node['_expanded'] && node["type"] != "initview" && node["type"] != "serverview" && node["type"] != "serviceview" && node["type"] != "cabinetview" && node["type"] != "networkdeviceview"){
            var api = "/api/comment/relation"
            var data = {"entity":node["type"],"value":node["id"]}
            json = jQuery.ajax({type:'GET',url:api,data:data,async:false});
            entity_nodes = jQuery.parseJSON(json.responseText);
            var links = topology.links
            var nodes = topology.nodes
//            console.log("length:"+nodes.length)
            var linksToDelete = []
            var nodesToDelete = []
//删掉所有与实体点连接的线
            links.forEach(function(link,index) {
                if(link["source"]["entity_type"] != "view" || link["target"]["entity_type"] != "view") {
                    linksToDelete.push(index)
                }
            });
//这里的reverse是一个技巧
//            console.log("length:"+topology.nodes.length)
            linksToDelete.reverse().forEach(function(index){
                links.splice(index,1);
            });

//删除所有实体点
//            console.log("length:"+topology.nodes.length)
            topology.nodes.forEach(function(node_) {
//                console.log("id:"+node_["id"])
                if(node_["entity_type"] != "view") {
                    nodesToDelete.push(node_["id"])
                }
            })
            nodesToDelete.forEach(function(node_) {
                topology.nodes.splice(topology.findNodeIndex(node_),1)
            })
            topology.update();


            buildNodes = []
            buildLinks = []
//如果该节点不是视图，则重建该节点与和视图的关系
            if (node["entity_type"] != "view") {
                entity_view_link = {}
                entity_father_view = node["type"] + "view"
                if (node["type"] == "raw" || node["type"] == "kvm" || node["type"] == "vm") {
                    entity_father_view = "serverview"
                }
                entity_view_link["source"] = entity_father_view
                entity_view_link["target"] = node["id"]
                buildNodes.push(node)
                buildLinks.push(entity_view_link)
            }
//如果该节点不是视图，重建该节点与子节点的关系，并将子节点和视图联系
            for (index in entity_nodes) {
                build_node = {}
                build_link = {}

                build_node["id"] = entity_nodes[index].id
                build_node["name"] = entity_nodes[index].name
                build_node["type"] = entity_nodes[index].type
                build_node["img"] = entity_nodes[index].img
                build_node["entity_type"] = entity_nodes[index].entity_type
                build_node["expand"] = true
                build_node["status"] = 1
                if (entity_nodes[index].vm_tag != undefined) {
                    build_node["vm_tag"] = entity_nodes[index].vm_tag
//                console.log("id:"+ entity_nodes[index].id + " tag:" + entity_nodes[index].vm_tag);
                }

                if (node["entity_type"] != "view")
                {
                    entity_father_view = build_node["type"] + "view"
                    if (build_node["type"] == "raw" || build_node["type"] == "kvm" || build_node["type"] == "vm") {
                        entity_father_view = "serverview"
                    }
                    entity_view_link =  {}
                    entity_view_link["source"] = entity_father_view
                    entity_view_link["target"] = build_node["id"]
//                    console.log("------link--------")
//                    console.log(entity_view_link)
                    buildLinks.push(entity_view_link)
                }

                build_link["source"] = node["id"]
                build_link["target"] = build_node["id"]
                buildLinks.push(build_link)
                buildNodes.push(build_node)


            }
            topology.addNodes(buildNodes)
            topology.addLinks(buildLinks)
            topology.nodes.forEach(function(node) {
                if (node["type"] == "vm") {
                    console.log("id:" + node["id"] + " vm_tag" + node["vm_tag"])
                }
            })
            topology.update();
//            topology.nodes = []
//            topology.links = []
//            topology.links.forEach(function(link){
//                console.log("source:" + link["source"]["id"])
//                console.log("target:" + link["target"]["id"])
//            })
//清空视图
//            topology.removeChildNodes("initview")

//增加initview
//            var view_node = []
//            var view_link = []
//            var master_node = {}
//            master_node["id"] = "initview"
//            master_node["name"] = "initview"
//            master_node["type"] = "initview"
//            master_node["entity_type"] = "view"
//            master_node["status"] = 1;
//            master_node["img"] = "/static/img/x2.jpg"
//            master_node["expand"] = true
//            master_node["_expanded"] = false
//            view_node.push(master_node)
//增加view视图
//            var api = "/api/comment/relation"
//            var data = {"entity":"initview","value":"initview"}
//            json = jQuery.ajax({type:'GET',url:api,data:data,async:false});
//            nodes = jQuery.parseJSON(json.responseText);
//            for (node_ in nodes)
//            {
//                child_node = {}
//                child_link = {}

//                child_node["id"] = nodes[node_]["id"]
//                child_node["name"] = nodes[node_]["name"]
//                child_node["type"] = nodes[node_]["type"]
//                child_node["img"] = nodes[node_]["img"]
//                child_node["expand"] = true
//                child_node["status"] = 1
//                child_node["entity_type"] = nodes[node_]["entity_type"]
//
//                child_link["source"] = master_node["id"]
//                child_link["target"] = child_node["id"]
//
//                view_node.push(child_node)
//                view_link.push(child_link)
//            }
//            topology.addNodes(view_node)
//            topology.addLinks(view_link)
//            topology.addNodes(node)
//            console.log("----------------after remove child node ------------------")
//            topology.nodes.forEach(function(node){
//                console.log("node:" + node["id"])
//            })
                

//增加视图节点
//            var view_node = []
//            var view_link = []
//            var master_node = {}
//            master_node["id"] = "initview"
//            master_node["name"] = "initview"
//            master_node["type"] = "initview"
//            master_node["entity_type"] = "view"
//            master_node["status"] = 1;
//            master_node["img"] = "/static/img/x2.jpg"
//            master_node["expand"] = true
//            master_node["_expanded"] = false

//            view_node.push(master_node)
//            var api = "/api/comment/relation"
//            var data = {"entity":"initview","value":"initview"}
//            json = jQuery.ajax({type:'GET',url:api,data:data,async:false});
//            viewnodes = jQuery.parseJSON(json.responseText);
//            for (node in nodes) {
//                child_node = {}
//                child_link = {}
//                child_node["id"] = nodes[node]["id"]
//                child_node["name"] = nodes[node]["name"]
//                child_node["type"] = nodes[node]["type"]
//                child_node["img"] = nodes[node]["img"]
//                child_node["expand"] = true
//                child_node["status"] = 1
//                child_node["entity_type"] = nodes[node]["entity_type"]

//                child_link["source"] = master_node["id"]
//                child_link["target"] = child_node["id"]

//                view_node.push(child_node)
//                view_link.push(child_link)
//            }
//            topology.addNodes(view_node)
//            topology.addLinks(view_link)
        }
    })
    
    topology.update();
}
            
//            var api = "/api/comment/relation"
//            var data = {"entity":node["type"],"value":node["id"]}
//            json = jQuery.ajax({type:'GET',url:api,data:data,async:false});
//            di_nodes = jQuery.parseJSON(json.responseText);
//            childNodes = []
//            childLinks = []
//            for (di_node in di_nodes)
//            {
//                child_node = {}
//                link = {}
//                child_node["id"] = di_nodes[di_node].id;
//                child_node["name"] = di_nodes[di_node].name;
//                child_node["type"] = di_nodes[di_node].type;
//                child_node["status"] = 1;
//                child_node["img"] = di_nodes[di_node].img
//                child_node["entity_type"] = di_nodes[di_node].entity_type
//                child_node["expand"] = true
//                console.log("entity_type:" + child_node["entity_type"])

//                link["source"] = node["id"]
//                link["target"] = child_node["id"]
//                childLinks.push(link)

//                entity_father_view = child_node["type"] + "view"
//                if (child_node["type"] == "raw" || child_node["type"] =="kvm" || child_node["type"] == "vm") {
//                    entity_father_view = "serverview"
//                }
//                entity_view_link = {}
//                entity_view_link["source"] = entity_father_view
//                entity_view_link["target"] = child_node["id"]
//                childLinks.push(entity_view_link)

//                var nodes = topology.nodes;
//                var find_node = false
//                for (var i in nodes){
//                    if (nodes[i]['id']== child_node["id"] )
//                    {
//                        find_node = true
//                    }
//                }
//                if (find_node == false) {
//                   childNodes.push(child_node)
//                }
//            }

//            var mynodes = []
//            var mylinks = []
//            mynodes.push(node)
//            var fatherNode;
//            topology.links.forEach(function(link,index){
//                if(link['target']["id"]== node["id"]) {
//                    fatherNode = link["source"]["id"];
//                }
//            });
//            save_link = {}
//            save_link["source"] = fatherNode
//            save_link["target"] = node["id"]
//            //entity links to delete
//           linksToDelete = []
//            //entity nodes to delete
//            entitynodeToDelete = []
//            mylinks.push(save_link)
//            topology.links.forEach(function(link,index){
//                var link_deleted = false
//                if (link['source']["entity_type"] != "view") {
//                console.log("++++++++index+++++++++")
//                console.log(link['source'])
//                console.log("+++++++++index end+++++++++")
//                    linksToDelete.push(index)
//                    link_deleted = true
//                    entitynodeToDelete.push(link['target']["id"]);
//               }
//                if (link['target']["entity_type"] != "view") {
//                    if (link_deleted == false) {
//                        linksToDelete.push(index);
//                    }
//                    in_delete = false
//                    for (var i in nodesToDelete){
//                        if (entitynodeToDelete[i] == link['target']["id"]) {
//                            in_delete = true
//                        }
//                    }
//                    if (in_delete == false) {
//                        entitynodeToDelete.push(link['target']["id"]);
//                    }
//                }
//            });
//            console.log("+++++++++link to delete+++++++++")
//            console.log(linksToDelete)
//            console.log("+++++++++link to delete end+++++++++")
//            //将要删除的node
//            nodesToDelete = []
//            nodes = topology.nodes;
//            entitynodeToDelete.forEach(function(node_id) {
//                for (var i in nodes) {
//                    if (nodes[i]['id'] == node_id) {
//                        index = i
//                        nodesToDelete.push(index)
//                    }
//                }
//            })
//            topology.removeChildNodes(node["id"]);
//            if ( node["entity_type"] != "view") {
//                linksToDelete.reverse().forEach(function(index){
//                    topology.links.splice(index,1);
//                });
//                nodesToDelete.reverse().forEach(function(index){
//                    topology.nodes.splice(index,1);
//                });
//                topology.addNodes(mynodes)
//                entity_father_view = node["type"] + "view"
//                if (node["type"] == "raw" || node["type"] =="kvm" || node["type"] == "vm") {
//                    entity_father_view = "serverview"
//                }
//                entity_view_link = {}
//                entity_view_link["source"] = entity_father_view
//                entity_view_link["target"] = node["id"]
//                var view_links = []
//                view_links.push(entity_view_link)
//                topology.addLinks(view_links)
//            }
//            if (childNodes.length > 0) {
//                topology.addNodes(childNodes);
//                topology.addLinks(childLinks);
//           }
//            nodes = topology.nodes
//            links = topology.links
//            console.log("=========================================")
//            nodes.forEach(function(node) {
//                console.log("id:" + node["id"])
//            }); 
//            console.log("link:" + links)
//            links.forEach(function(link) {
//                console.log("link:" + link)
//                console.log("source:" + link["source"]["id"])
//                console.log("target:" + link["target"]["id"])
//            });
//            for(var i=nodes.length-1;i>=0;i--){
//                var haveFoundNode=false;
//                for(var j=0,l=links.length;j<l;j++){
//                    ( links[j]['source']==nodes[i] || links[j]['target']==nodes[i] ) && (haveFoundNode=true)
//                }
//                !haveFoundNode && nodes.splice(i,1);
//            }
//            topology.update();
//        }
//    });

//    topology.update();
//}

function expandNode(id){
    topology.addNodes(childNodes);
    topology.addLinks(childLinks);
    topology.update();
}

function collapseNode(id){
    topology.removeChildNodes(id);
    topology.update();
}
