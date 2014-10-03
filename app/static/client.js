var app = angular.module('App',[]);

// Change angular html template tags to avoid conflict with flask
app.config(function($interpolateProvider) {
  $interpolateProvider.startSymbol('[[');
  $interpolateProvider.endSymbol(']]');
});

app.controller('Ctrl', function($scope, socket) {


    // scoket listenters
    socket.on('status', function (data) {
        // application logic ....
        $scope.status = data.msg;
    });

    // scoket listenters
    socket.on('push', function (data) {
        // application logic ....
        d = JSON.parse(data);
        // d = data;

        // var a = d.data.split(",");
        $scope.data = d;
        // $scope.data.avePre
        // console.log(typeof(d));
    });

    $scope.count = function(){
        socket.emit('count');
        return false;
    }
    $scope.clear = function(){
        socket.emit('clear');
        return false;
    }
    $scope.changeAve = function(){
        socket.emit('changeAve', {avewindow: $scope.avewindow});
        return false;
    }
$scope.avewindow = 40;
$scope.middle = 0;
$scope.range = 60; 
var n = 50,
    duration = 200,
    now = new Date(Date.now() - duration),
    count = 0,
    data = d3.range(n).map(function() { return 0; });
var margin = {top: 20, right: 80, bottom: 20, left: 0},
    width = 360 - margin.left - margin.right,
    height = 360 - margin.top - margin.bottom;

 
var drawing = false;
// var x = d3.scale.linear()
//     .domain([1, n - 2])
//     .range([0, width]);

var x = d3.time.scale()
    .domain([now - (n - 2) * duration, now - duration])
    .range([0, width]);

var y = d3.scale.linear()
    .domain([1, 0])
    .range([height, 0]);

var line = d3.svg.line()
    .interpolate("basis")
    .x(function(d, i) { return x(now - (n - 1 - i) * duration); })
    .y(function(d, i) { return y(d); });

var svg = d3.select("#chart").append("svg")
    .attr("id", "linechart")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
svg.append("circle")
    .attr("id", "backrect")
    .attr("r", "20")
    .attr("fill", "white")
    .attr("cx", width * 0.8)
    .attr("cy", height * 0.1)



svg.append("defs").append("clipPath")
    .attr("id", "clip")
  .append("rect")
    .attr("width", width)
    .attr("height", height);

var axis = svg.append("g")
    .attr("class", "x axis")
    .attr("transform", "translate(0," + height + ")")
    .call(x.axis = d3.svg.axis().scale(x).orient("bottom"));

svg.append("g")
    .attr("class", "y axis")
    .attr("transform", "translate(" + width + " ,0)")
    .call(y.axis= d3.svg.axis().scale(y).orient("right"));

var path = svg.append("g")
    .attr("clip-path", "url(#clip)")
  .append("path")
    .datum(data)
    .attr("class", "line")
    .attr("d", line);

d3.select("g").append("foreignObject")
    .attr("id", "charap")
    .attr("width", "69px")
    .attr("height", "120px")
    .attr("x",0)
    .attr("y",-10)
    .html("<p class='chara'></p>");    


// setTimeout(tick(), 1000);

tick();

function tick() {
    if($scope.data){
    console.log($scope.data);
    }else{
      console.log("No data");
    }

  var d = $scope.data?$scope.data.avePres:0;
  // push a new data point onto the back
  now = new Date();
  x.domain([now - (n - 2) * duration, now - duration]);


  // y.domain([d3.max(data), d3.min(data)])
  //   .range([height, 0]);

  data.push(d);

  var first = Math.floor(d3.max(d3.values(data)));

  if(drawing == false && first != 0){
    $scope.middle = first;
    drawing = true;
    panel();

  }

  y.domain([$scope.middle + $scope.range/2, $scope.middle - $scope.range/2])
    .range([height, 0]);

  svg.selectAll("g.y.axis")
      .call(y.axis);

  // redraw the line, and slide it to the left
  svg.select(".line")
      .attr("d", line)
      .attr("transform", null);

  // slide the x-axis left
  axis.transition()
      .duration(duration)
      .ease("linear")
      .call(x.axis);

  // slide the line left
  path.transition()
      .duration(duration)
      .ease("linear")
      .attr("transform", "translate(" + x(now - (n - 1) * duration) + ")")
      .each("end", tick);


charay = (data[24] + $scope.range/2 - $scope.middle)/$scope.range * height - 100;
d3.select("#charap").transition()
        .duration(100)
        .attr("x",width /2 - 40)
        .attr("y", charay);
        //.attr("transform","translate(150,"+ charay+")");


  // pop the old data point off the front
  data.shift();
}



function panel(){
// Set Up
  var pi = Math.PI; var iR=170;  var oR=110;
  var margin = {top: 20, right: 5, bottom: 20, left: 5},
    width = 360 - margin.left - margin.right,
    height = 400 - margin.top - margin.bottom;
  var cur_color = 'limegreen';  var new_color, hold; 
  var max = Math.floor($scope.middle + $scope.range/2), min = Math.floor($scope.middle - $scope.range/2), current = Math.floor($scope.middle);
  var arc = d3.svg.arc().innerRadius(iR).outerRadius(oR).startAngle(-90 * (pi/180)); // Arc Defaults
  // Place svg element
  var svg = d3.select("#chart").append("svg").attr("width", width).attr("height", height)
    .append("g").attr("transform", "translate(" + width / 2 + "," + height / 2 + ")")
  var background = svg.append("path").datum({endAngle:  90 * (pi/180)}).style("fill", "#ddd").attr("d", arc);// Append background arc to svg
  var foreground = svg.append("path").datum({endAngle: -90 * (pi/180)}).style("fill", cur_color).attr("d", arc); // Append foreground arc to svg
  var max = svg.append("text").attr("transform", "translate("+ (iR + ((oR - iR)/2)) +",15)") // Display Max value
  .attr("text-anchor", "middle").style("font-family", "Helvetica").text(max) // Set between inner and outer Radius
  // Display Min value
  var min = svg.append("text").attr("transform", "translate("+ -(iR + ((oR - iR)/2)) +",15)") // Set between inner and outer Radius
              .attr("text-anchor", "middle").style("font-family", "Helvetica").text(min)
  // Display Current value
  var current = svg.append("text").attr("transform", "translate(0,"+ -(iR/4) +")") // Push up from center 1/4 of innerRadius
              .attr("text-anchor", "middle").style("font-size", "50").style("font-family", "Helvetica").text(current)
  // Update every x seconds
  setInterval(function() {
  pres = Math.floor($scope.data.avePres);
  cupa = pres;
  pres = (pres > $scope.middle + $scope.range/2)?$scope.middle + $scope.range/2:pres;
  pres = (pres < $scope.middle - $scope.range/2)?$scope.middle + $scope.range/2:pres;
  var num = pres; var numPi = (num - $scope.middle)  * (pi/$scope.range);// Get value
  if((num - $scope.middle + $scope.range/2)  >= $scope.range*2/3) {new_color = 'limegreen';} else if(num - $scope.middle + $scope.range/2 >= $scope.range/3) {new_color = 'orange';} else {new_color = 'red';} // Get new color
  current.transition().text(Math.floor(cupa));// Text transition
  max.transition().text(Math.floor($scope.middle + $scope.range/2));// Text transition
  min.transition().text(Math.floor($scope.middle - $scope.range/2));// Text transition
  // Arc Transition
  foreground.transition().duration(750).styleTween("fill", function() { return d3.interpolate(new_color, cur_color); }).call(arcTween, numPi);
    // Set colors for next transition
  hold = cur_color; cur_color = new_color; new_color = hold;
  d3.select("#backrect").attr("fill", new_color);
  }, 1000); // Repeat every 1s
  function arcTween(transition, newAngle) {
    transition.attrTween("d", function(d) {var interpolate = d3.interpolate(d.endAngle, newAngle);
              return function(t) {d.endAngle = interpolate(t);  return arc(d);  };  }); } // Update animation
  }
});

app.factory('socket', function ($rootScope) {
  var socket = io.connect('http://' + document.domain + ':' + location.port + '/main');
  return {
    on: function (eventName, callback) {
      socket.on(eventName, function () {
        var args = arguments;
        $rootScope.$apply(function () {
          callback.apply(socket, args);
        });
      });
    },
    emit: function (eventName, data, callback) {
      socket.emit(eventName, data, function () {
        var args = arguments;
        $rootScope.$apply(function () {
          if (callback) {
            callback.apply(socket, args);
          }
        });
      })
    }
  };
});

