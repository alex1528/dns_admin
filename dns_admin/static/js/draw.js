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
      .data(this.nodes, function(d) { return d.id;});

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
      .on('click',function(d){ d.expand && self.clickFn(d);})

  nodeEnter.append("svg:text")
      .attr("class", "nodetext")
      .attr("dx", 15)
      .attr("dy", -35)
      .text(function(d) { return d.id });

  
  node.exit().remove();

  this.force.start();
}




//var nodes=[
//    {id:'vmh0.hy01',type:'router',status:1},
//    {id:'app0.hy01',type:'switch',status:1,expand:true},
//    {id:'app1.hy01',type:'switch',status:1},
//    {id:'app2.hy01',type:'switch',status:0}

//];


//var links=[
//    {source:'vmh0.hy01',target:'app0.hy01'},
//    {source:'vmh0.hy01',target:'app1.hy01'},
//    {source:'vmh0.hy01',target:'app2.hy01'}
//];




//可展开节点的点击事件
//topology.setNodeClickFn(function(node){
//    if(!node['_expanded']){
//        var api = "/api/comment/relation"
//        var data = {"entity":node["type"],"value":node["id"]}
//        json = jQuery.ajax({type:'GET',url:api,data:data,async:false});
//        alert(json);
//        expandNode(node.id);
//        node['_expanded']=true;
//    }else{
//        collapseNode(node.id);
//        node['_expanded']=false;
//    }
//});
function buildNode(container,nodes,links){
    var topology=new Topology(container);
    topology.addNodes(nodes);
    topology.addLinks(links);
    topology.update();
}
function indexNodeA(container,nodes,links){
    var topology=new Topology(container);
    topology.addNodes(nodes);
    topology.addLinks(links);
    topology.setNodeClickFn(function(node){
        if(!node['_expanded']){
          //  alert(node["id"]);
           // alert(node["type"]);
            var api = "/api/comment/relation"
            var data = {"entity":node["type"],"value":node["id"]}
//            var data = {"entity":"service","value":"api"}
            json = jQuery.ajax({type:'GET',url:api,data:data,async:false});
//            alert(json);
            di_nodes = jQuery.parseJSON(json.responseText);
            childNodes = []
            childLinks = []
            for (di_node in di_nodes)
            {
                child_node = {}
                link = {}
                child_node["id"] = di_nodes[di_node].name;
                child_node["type"] = di_nodes[di_node].type;
                child_node["status"] = 0;
                child_node["img"] = "/static/img/" + di_nodes[di_node].type +".png"
                child_node["expand"] = true

                link["source"] = node["id"]
                link["target"] = child_node["id"]
                childLinks.push(link)
                childNodes.push(child_node)
            }

            var mynodes = []
            var mylinks = []
            mynodes.push(node)
            var fatherNode;
            //得到父节点的id
            topology.links.forEach(function(link,index){
                if(link['target']["id"]== node["id"]) {
                    fatherNode = link["source"]["id"];
                }
            });
            save_link = {}
            save_link["source"] = fatherNode
            save_link["target"] = node["id"]
            //将要删除的link
            linksToDelete = []
            //兄弟节点的id
            brotherNodes = []
            mylinks.push(save_link)
            topology.links.forEach(function(link,index){
                link['source']["id"]== fatherNode
                && linksToDelete.push(index)
                && brotherNodes.push(link['target']["id"]);
            });
            //将要删除的node
            nodesToDelete = []
            nodes = topology.nodes;
            brotherNodes.forEach(function(node_id) {
                for (var i in nodes) {
                    if (nodes[i]['id'] == node_id) {
                        index = i
                        nodesToDelete.push(index)
                    }
                }
            })
            topology.removeChildNodes(node["id"]);
            //删掉兄弟节点和自己与父节点的link
            linksToDelete.reverse().forEach(function(index){
                topology.links.splice(index,1);
            });
            nodesToDelete.reverse().forEach(function(index){
                topology.nodes.splice(index,1);
            });
            topology.addNodes(mynodes)
            topology.addLinks(mylinks)
            if (childNodes.length > 0) {
                topology.addNodes(childNodes);
                topology.addLinks(childLinks);
            }
            //alert("begin")
            //topology.nodes.forEach(function(node_obj) {
            //    alert(node_obj["id"]);
            //});
            //topology.links.forEach(function(link_obj) {
              //  alert("source:" + link_obj["source"]["id"] + "target:" + link_obj["target"]["id"]);
            //})
            //alert("end");
            topology.update();
        }
    });

    topology.update();
}

function expandNode(id){
    topology.addNodes(childNodes);
    topology.addLinks(childLinks);
    topology.update();
}

function collapseNode(id){
    topology.removeChildNodes(id);
    topology.update();
}
