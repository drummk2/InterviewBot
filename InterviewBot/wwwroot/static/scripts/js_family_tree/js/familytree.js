// extend javascript array class by a remove function
// copied from https://stackoverflow.com/a/3955096/12267732
Array.prototype.remove = function() {
    var what, a = arguments,
        L = a.length,
        ax;
    while (L && this.length) {
        what = a[--L];
        while ((ax = this.indexOf(what)) !== -1) {
            this.splice(ax, 1);
        }
    }
    return this;
};

function d3_append_multiline_text(d3element, text, delimiter = "_", css_class = undefined, line_sep = 14,
    line_offset = undefined, x = 13, dominant_baseline = "central") {
    if (!text) return;
    const d3text = d3element.append("text")
        .attr("class", css_class)
        .attr("dominant-baseline", dominant_baseline);
    const arr = text.split(delimiter);
    if (!line_offset) { line_offset = -line_sep * (arr.length - 1) / 2; }
    if (arr != undefined) {
        for (let i = 0; i < arr.length; i++) {
            d3text.append("tspan")
                .text(arr[i])
                .attr("dy", i == 0 ? line_offset : line_sep)
                .attr("x", x);
        }
    }
};

class FTDataHandler {
    constructor(data, start_node_id = data.start) {
        if (data.links.length > 0) {

            this.dag = d3.dagConnect()(data.links);

            if (this.dag.id != undefined) {
                this.root = this.dag.copy();
                this.root.id = undefined;
                this.root.children = [this.dag];
                this.dag = this.root;
            }

            this.nodes = this.dag.descendants().map(node => {
                if (node.id in data.unions) return new Union(node, this)
                else if (node.id in data.persons) return new Person(node, this);
            });

            this.nodes.forEach(n => n._children = n._children.map(c => c.ftnode));

            this.number_nodes = 0;
            this.nodes.forEach(node => {
                node.id = node.id || this.number_nodes;
                this.number_nodes++;
            })

            this.root = this.find_node_by_id(start_node_id);
            this.root.visible = true;
            this.dag.children = [this.root];

        }
        else if (Object.values(data.persons).length > 0) {

            const root_data = data.persons[start_node_id];
            this.root = new d3.dagNode(start_node_id, root_data);
            this.root = new Person(this.root, this);
            this.root.visible = true;
            this.number_nodes = 1;
            this.nodes = [this.root];

            this.dag = new d3.dagNode(undefined, {});
            this.dag.children = this.root;
        }
    };

    update_roots() {
        this.dag.children = [this.root];
        const FT = this;

        function find_roots_recursive(node) {
            node.get_visible_inserted_neighbors().forEach(node => {
                if (node.is_root()) FT.dag.children.push(node);
                find_roots_recursive(node);
            });
        };
        find_roots_recursive(this.root);
    };

    find_node_by_id(id) {
        return this.nodes.find(node => node.id == id);
    };
};

class FTNode extends d3.dagNode {
    is_extendable() {
        return this.get_neighbors().filter(node => !node.visible).length > 0;
    };

    get_visible_neighbors() {
        return this.get_neighbors().filter(node => node.visible);
    }

    get_visible_inserted_neighbors() {
        return this.get_visible_neighbors().filter(node => this.inserted_nodes.includes(node));
    };
};

class Union extends FTNode {
    constructor(dagNode, ft_datahandler) {
        super(dagNode.id, data.unions[dagNode.id]);
        dagNode.ftnode = this;
        this.ft_datahandler = ft_datahandler;
        this._children = dagNode.children;
        this.children = [];
        this._childLinkData = dagNode._childLinkData;
        this.inserted_nodes = [];
        this.inserted_links = [];
        this.visible = false;
    };

    get_neighbors() {
        return this.get_parents().concat(this.get_children())
    };

    get_parents() {
        var parents = this.data.partner
            .map(id => this.ft_datahandler.find_node_by_id(id))
            .filter(node => node != undefined);
        if (parents) return parents
        else return [];
    }

    get_hidden_parents() {
        return this.get_parents().filter(parent => !parent.visible);
    };

    get_visible_parents() {
        return this.get_parents().filter(parent => parent.visible);
    };

    get_children() {
        var children = [];
        children = this.children.concat(this._children);
        children = children
            .filter(c => c != undefined)
        return children
    };

    get_hidden_children() {
        return this.get_children().filter(child => !child.visible);
    };

    get_visible_children() {
        return this.get_children().filter(child => child.visible);
    };

    show_child(child) {
        if (!this._children.includes(child)) {
            console.warn("Child node not in this' _children array.");
        }
        this.children.push(child);
        this._children.remove(child);

        if (child.visible) {
            this.inserted_links.push([this, child]);
        }
        else {
            child.visible = true;
            this.inserted_nodes.push(child);
        }
    };

    show_parent(parent) {
        if (!parent._children.includes(this)) {
            console.warn("This node not in parent's _children array.");
        }
        parent.children.push(this);
        parent._children.remove(this);
        if (parent.visible) {
            this.inserted_links.push([parent, this]);
        }
        else {
            parent.visible = true;
            this.inserted_nodes.push(parent);
        }
    };

    show() {
        this.visible = true;

        this.get_children().forEach(child => {
            this.show_child(child);
        });

        this.get_parents().forEach(parent => {
            this.show_parent(parent);
        });

    };

    get_visible_inserted_children() {
        return this.children.filter(child => this.inserted_nodes.includes(child));
    };

    get_visible_inserted_parents() {
        return this.get_visible_parents().filter(parent => this.inserted_nodes.includes(parent));
    };

    is_root() {
        return false;
    }

    hide_child(child) {
        if (!this.children.includes(child)) {
            console.warn("Child node not in this' children array.");
        }
        child.visible = false;
        this._children.push(child);
        this.children.remove(child);
        this.inserted_nodes.remove(child);
    };

    hide_parent(parent) {
        if (!parent.children.includes(this)) {
            console.warn("This node not in parent's children array.");
        }
        parent.visible = false;
        parent._children.push(this);
        parent.children.remove(this);
        this.inserted_nodes.remove(parent);
    };

    hide() {
        this.visible = false;

        this.get_visible_inserted_children().forEach(child => {
            this.hide_child(child);
        });

        this.get_visible_inserted_parents().forEach(parent => {
            this.hide_parent(parent);
        });

        this.inserted_links.forEach(edge => {
            const source = edge[0];
            const target = edge[1];
            if (this == source) {
                this._children.push(target);
                this.children.remove(target);
            } else if (this == target) {
                source._children.push(this);
                source.children.remove(this);
            };
        });
        this.inserted_links = [];

    };

    get_own_unions() {
        return [];
    };

    get_parent_unions() {
        return [];
    };

    get_name() {
        return undefined;
    };

    get_birthyear() {
        return undefined;
    };

    get_birth_place() {
        return undefined;
    };

    get_death_year() {
        return undefined;
    };

    get_death_place() {
        return undefined;
    };

    is_union() {
        return true;
    };

    add_parent(person_data) {
        const id = person_data.id || "p" + ++this.ft_datahandler.number_nodes;
        const dagNode = new d3.dagNode(id, person_data);
        const person = new Person(dagNode, this.ft_datahandler);
        if (!("parent_union" in person_data)) person_data.parent_union = undefined;
        if (!("own_unions" in person_data)) {
            person_data.own_unions = [this.id];
            person._childLinkData = [
                [person.id, this.id]
            ];
            person._children.push(this);
        }

        person.data = person_data;
        this.ft_datahandler.nodes.push(person);
        if (!person_data.own_unions.includes(this.id)) person_data.own_unions.push(this.id);
        if (!this.data.partner.includes(person.id)) this.data.partner.push(person.id);
        this.show_parent(person);
        this.ft_datahandler.update_roots();
        return person;
    };

    add_child(person_data) {
        const id = person_data.id || "p" + ++this.ft_datahandler.number_nodes;
        const dagNode = new d3.dagNode(id, person_data);
        const person = new Person(dagNode, this.ft_datahandler);
        if (!("parent_union" in person_data)) person_data.parent_union = this.id;
        if (!("own_unions" in person_data)) person_data.own_unions = [];
        person.data = person_data;
        this.ft_datahandler.nodes.push(person);
        if (!person_data.parent_union == this.id) person_data.parent_union == this.id;
        if (!this.data.children.includes(person.id)) this.data.children.push(person.id);
        if (!this._childLinkData.includes([this.id, person.id])) this._childLinkData.push([this.id, person.id]);
        this.show_child(person);
        return person;
    }
};

class Person extends FTNode {
    constructor(dagNode, ft_datahandler) {
        super(dagNode.id, data.persons[dagNode.id]);
        dagNode.ftnode = this;
        this.ft_datahandler = ft_datahandler;
        this._children = dagNode.children;
        this.children = [];
        this._childLinkData = dagNode._childLinkData;
        this.inserted_nodes = [];
        this.inserted_links = [];
        this.visible = false;
    };

    get_name() {
        return this.data.name;
    };

    get_birthyear() {
        return this.data.birthyear;
    };

    get_birth_place() {
        return this.data.birthplace;
    };

    get_death_year() {
        return this.data.deathyear;
    };

    get_death_place() {
        return this.data.deathplace;
    };

    get_neighbors() {
        return this.get_own_unions().concat(this.get_parent_unions());
    };

    get_parent_unions() {
        var unions = [this.data.parent_union]
            .map(id => this.ft_datahandler.find_node_by_id(id))
            .filter(node => node != undefined);
        var u_id = this.data.parent_union;
        if (unions) return unions
        else return [];
    };

    get_hidden_parent_unions() {
        return this.get_parent_unions().filter(union => !union.visible);
    };

    get_visible_parent_unions() {
        return this.get_parent_unions().filter(union => union.visible);
    };

    get_visible_inserted_parent_unions() {
        return this.get_visible_parent_unions().filter(union => this.inserted_nodes.includes(union));
    };

    is_root() {
        return this.get_visible_parent_unions().length == 0;
    };

    is_union() {
        return false;
    };

    get_own_unions() {
        var unions = (this.data.own_unions ?? [])
            .map(id => this.ft_datahandler.find_node_by_id(id))
            .filter(u => u != undefined);
        if (unions) return unions
        else return [];
    };

    get_hidden_own_unions() {
        return this.get_own_unions().filter(union => !union.visible);
    };

    get_visible_own_unions() {
        return this.get_own_unions().filter(union => union.visible);
    };

    get_visible_inserted_own_unions() {
        return this.get_visible_own_unions().filter(union => this.inserted_nodes.includes(union));
    };

    get_parents() {
        var parents = [];
        this.get_parent_unions().forEach(
            u => parents = parents.concat(u.get_parents())
        );
    };

    get_other_partner(union_data) {
        var partner_id = union_data.partner.find(
            p_id => p_id != this.id & p_id != undefined
        );
        return all_nodes.find(n => n.id == partner_id)
    };

    get_partners() {
        var partners = [];
        this.get_own_unions().forEach(
            u => {
                partners.push(this.get_other_partner(u.data))
            }
        )
        return partners.filter(p => p != undefined)
    };

    get_children() {
        var children = [];
        this.get_own_unions().forEach(
            u => children = children.concat(getChildren(u))
        )
        children = children.filter(c => c != undefined)
        return children
    };

    show_union(union) {
        union.show();
        this.inserted_nodes.push(union);
    };

    hide_own_union(union) {
        union.hide();
        this.inserted_nodes.remove(union);
    };

    hide_parent_union(union) {
        union.hide();
    };

    show() {
        this.get_hidden_own_unions().forEach(union => this.show_union(union));
        this.get_hidden_parent_unions().forEach(union => this.show_union(union));
    };

    hide() {
        this.get_visible_inserted_own_unions().forEach(union => this.hide_own_union(union));
        this.get_visible_inserted_parent_unions().forEach(union => this.hide_parent_union(union));
    };

    click() {
        if (this.is_extendable()) this.show();
        else this.hide();
        this.ft_datahandler.update_roots();
    };

    add_own_union(union_data) {
        const id = union_data.id || "u" + ++this.ft_datahandler.number_nodes;
        const dagNode = new d3.dagNode(id, union_data);
        const union = new Union(dagNode, this.ft_datahandler);
        if (!("partner" in union_data)) union_data.partner = [this.id];
        if (!("children" in union_data)) {
            union_data.children = [];
            union._childLinkData = [];
        }

        union.data = union_data;
        this.ft_datahandler.nodes.push(union);

        if (!union_data.partner.includes(this.id)) union_data.partner.push(this.id);

        if (!this.data.own_unions.includes(union.id)) this.data.own_unions.push(union.id);
        if (!this._childLinkData.includes([this.id, union.id])) this._childLinkData.push([this.id, union.id]);

        this.show_union(union);
        return union;
    };

    add_parent_union(union_data) {
        const id = union_data.id || "u" + ++this.ft_datahandler.number_nodes;
        const dagNode = new d3.dagNode(id, union_data);
        const union = new Union(dagNode, this.ft_datahandler);
        if (!("partner" in union_data)) union_data.partner = [];
        if (!("children" in union_data)) {
            union_data.children = [this.id];
            union._childLinkData = [
                [union.id, this.id]
            ];
            union._children.push(this);
        }
        union.data = union_data;
        this.ft_datahandler.nodes.push(union);

        if (!union_data.children.includes(this.id)) union_data.children.push(this.id);

        this.data.parent_union = union.id;

        this.show_union(union);
        this.ft_datahandler.update_roots();
        return union;
    };
};

class FTDrawer {
    static label_delimiter = "_";

    constructor(
        ft_datahandler,
        svg,
        x0,
        y0,
    ) {
        this.ft_datahandler = ft_datahandler;
        this.svg = svg;
        this._orientation = null;
        this.link_css_class = "link";

        this.g = this.svg.append("g");

        this.zoom = d3.zoom().on("zoom", event => this.g.attr("transform", event.transform));
        this.svg.call(this.zoom);

        this._tooltip_div = d3.select("div#main-container > div#family-tree-container-border-wrapper > div#family-tree-container").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        this.tooltip(FTDrawer.default_tooltip_func);

        this.layout = d3.sugiyama()
            .nodeSize([120, 120])
            .layering(d3.layeringSimplex())
            .decross(d3.decrossOpt)
            .coord(d3.coordVert());

        this.orientation("horizontal");
        this.transition_duration(750);
        this.link_path(FTDrawer.default_link_path_func);
        this.node_label(FTDrawer.default_node_label_func);
        this.node_size(FTDrawer.default_node_size_func);
        this.node_class(FTDrawer.default_node_class_func);

        const default_pos = this.default_root_position();
        this.ft_datahandler.root.x0 = x0 || default_pos[0];
        this.ft_datahandler.root.y0 = y0 || default_pos[1];
    };

    default_root_position() {
        return [
            window.innerWidth / 2,
            window.innerHeight / 2
        ];
    }

    orientation(value) {
        if (!value) return this.orientation;
        else {
            this._orientation = value;
            return this;
        }
    };

    node_separation(value) {
        if (!value) return this.layout.nodeSize();
        else {
            this.layout.nodeSize(value);
            return this;
        }
    };

    layering(value) {
        if (!value) return this.layout.layering();
        else {
            this.layout.layering(value);
            return this;
        }
    };

    decross(value) {
        if (!value) return this.layout.decross();
        else {
            this.layout.decross(value);
            return this;
        }
    };

    coord(value) {
        if (!value) return this.layout.coord();
        else {
            this.layout.coord(value);
            return this;
        }
    };

    transition_duration(value) {
        if (value != 0 & !value) return this._transition_duration;
        else {
            this._transition_duration = value;
            return this;
        }
    };

    static default_tooltip_func(node) {
        if (node.is_union()) return;
        var content = `
                <span style='margin-left: 2.5px;'><b>` + node.get_name() + `</b></span><br>
                <table style="margin-top: 2.5px;">
                        <tr><td>born</td><td>` + (node.get_birthyear() || "?") + ` in ` + (node.data.birthplace || "?") + `</td></tr>
                        <tr><td>died</td><td>` + (node.get_death_year() || "?") + ` in ` + (node.data.deathplace || "?") + `</td></tr>
                </table>
                `
        return content.replace(new RegExp("null", "g"), "?");
    };

    tooltip(tooltip_func) {
        if (!tooltip_func) {
            this.show_tooltips = false;
        } else {
            this.show_tooltips = true;
            this._tooltip_func = tooltip_func;
        }
        return this;
    };

    static default_node_label_func(node) {
        if (node.is_union()) return;
        return node.get_name() +
            FTDrawer.label_delimiter +
            (node.get_birthyear() || "?") + " - " + (node.get_death_year() || "?");
    };

    node_label(node_label_func) {
        if (!node_label_func) {} else { this.node_label_func = node_label_func };
        return this;
    };

    static default_node_class_func(node) {
        if (node.is_union()) return;
        else {
            if (node.is_extendable()) return "person extendable"
            else return "person non-extendable"
        };
    };

    node_class(node_class_func) {
        if (!node_class_func) {} else { this.node_class_func = node_class_func };
        return this;
    };

    static default_node_size_func(node) {
        if (node.is_union()) return 0;
        else return 10;
    }

    node_size(node_size_func) {
        if (!node_size_func) {} else { this.node_size_func = node_size_func };
        return this;
    };

    static default_link_path_func(s, d) {
        function vertical_s_bend(s, d) {
            return `M ${s.x} ${s.y} 
            C ${s.x} ${(s.y + d.y) / 2},
            ${d.x} ${(s.y + d.y) / 2},
            ${d.x} ${d.y}`
        }

        function horizontal_s_bend(s, d) {
            return `M ${s.x} ${s.y}
            C ${(s.x + d.x) / 2} ${s.y},
              ${(s.x + d.x) / 2} ${d.y},
              ${d.x} ${d.y}`
        }

        return this._orientation == "vertical" ? vertical_s_bend(s, d) : horizontal_s_bend(s, d);
    }

    link_path(link_path_func) {
        if (!link_path_func) {} else { this.link_path_func = link_path_func };
        return this;
    }

    static make_unique_link_id(link) {
        return link.id || link.source.id + "_" + link.target.id;
    }

    draw(source = this.ft_datahandler.root) {
        const nodes = this.ft_datahandler.dag.descendants(),
              links = this.ft_datahandler.dag.links();

        this.layout(this.ft_datahandler.dag);

        if (this._orientation == "horizontal") {
            var buffer = null;
            nodes.forEach(function(d) {
                buffer = d.x
                d.x = d.y;
                d.y = buffer;
            });
        }

        var node = this.g.selectAll('g.node')
            .data(nodes, node => node.id)

        var nodeEnter = node.enter().append('g')
            .attr('class', 'node')
            .attr("transform", _ => "translate(" + source.x0 + "," + source.y0 + ")")
            .on('click', (_, node) => {
                node.click();
                this.draw(node);
            })
            .attr('visible', true);

        if (this.show_tooltips) {
            const tooltip_div = this._tooltip_div,
                  tooltip_func = this._tooltip_func;
            nodeEnter
                .on("mouseover", function (event, d) {
                    tooltip_div.transition()
                        .duration(200)
                        .style("opacity", undefined);
                    tooltip_div.html(tooltip_func(d));
                    let height = tooltip_div.node().getBoundingClientRect().height;
                    tooltip_div.style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY-height/2) + "px");
                })
                .on("mouseout", function (d) {
                    tooltip_div.transition()
                        .duration(500)
                        .style("opacity", 0);
                });
        };

        nodeEnter.append('circle')
            .attr('class', this.node_class_func)
            .attr('r', 1e-6)

        const this_object = this;
        nodeEnter.each(function(node) {
            d3_append_multiline_text(
                d3.select(this),
                this_object.node_label_func(node),
                FTDrawer.label_delimiter,
                "node-label",
            )
        });

        var nodeUpdate = nodeEnter.merge(node);

        nodeUpdate.transition()
            .duration(this.transition_duration())
            .attr("transform", d => "translate(" + d.x + "," + d.y + ")");

        nodeUpdate.select('.node circle')
            .attr('r', this.node_size_func)
            .attr('class', this.node_class_func)
            .attr('cursor', 'pointer');

        var nodeExit = node.exit().transition()
            .duration(this.transition_duration())
            .attr("transform", _ => "translate(" + source.x + "," + source.y + ")")
            .attr('visible', false)
            .remove();

        nodeExit.select('circle')
            .attr('r', 1e-6);

        nodeExit.select('text')
            .style('fill-opacity', 1e-6);

        var link = this.g.selectAll('path.' + this.link_css_class)
            .data(links, FTDrawer.make_unique_link_id);

        var linkEnter = link.enter().insert('path', "g")
            .attr("class", this.link_css_class)
            .attr('d', _ => {
                var o = {
                    x: source.x0,
                    y: source.y0
                }
                return this.link_path_func(o, o)
            });

        var linkUpdate = linkEnter.merge(link);

        linkUpdate.transition()
            .duration(this.transition_duration())
            .attr('d', d => this.link_path_func(d.source, d.target));

        var linkExit = link.exit().transition()
            .duration(this.transition_duration())
            .attr('d', _ => {
                var o = {
                    x: source.x,
                    y: source.y
                }
                return this.link_path_func(o, o)
            })
            .remove();

        this.svg.transition()
            .duration(this.transition_duration())
            .call(
                this.zoom.transform,
                d3.zoomTransform(this.g.node()).translate(-(source.x - source.x0), -(source.y - source.y0)),
            );

        nodes.forEach(function(d) {
            d.x0 = d.x;
            d.y0 = d.y;
        });

    };

    clear() {
        this.g.selectAll("*").remove();
    }
};

class FamilyTree extends FTDrawer {

    constructor(data, svg) {
        const ft_datahandler = new FTDataHandler(data);
        super(ft_datahandler, svg);
        this.treeCentred = false;
    };

    get root() {
        return this.ft_datahandler.root;
    }

    wait_until_data_loaded(old_data, delay, tries, max_tries) {
        if (tries == max_tries) {
            return;
        } else {
            const new_data = window.data;
            if (old_data == new_data) {
                setTimeout(
                    _ => this.wait_until_data_loaded(old_data, delay, ++tries, max_tries),
                    delay,
                )
            } else {
                this.draw_data(new_data);
                return;
            }
        }
    }

    draw_data(data) {
        var x0 = null,
            y0 = null;
        if (this.root !== null) {
            [x0, y0] = [this.root.x0, this.root.y0];
        } else {
            [x0, y0] = this.default_root_position();
        }
        this.ft_datahandler = new FTDataHandler(data);
        this.root.x0 = x0;
        this.root.y0 = y0;
        this.clear();
        this.draw();
    }

    get_data(data_url) {
        let request = new XMLHttpRequest()
        request.open("GET", data_url)

        request.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                return JSON.parse(request.responseText);
            }
        }

        request.send()
    }

    load_data(path_to_data) {
        const old_data = data,
            max_tries = 5,
            delay = 1000,
            file = document.createElement('script');
        var tries = 0;
        file.onreadystatechange = function() {
            if (this.readyState == 'complete') {
                this.wait_until_data_loaded(old_data, delay, tries, max_tries);
            }
        }
        file.type = "text/javascript";
        file.src = path_to_data;
        file.onload = this.wait_until_data_loaded(old_data, delay, tries, max_tries);
        document.getElementsByTagName("head")[0].appendChild(file)
    }

    load_data_from_endpoint(endpoint_url) {
        var self = this;
        let request = new XMLHttpRequest()
        request.open("GET", endpoint_url)

        request.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                var new_data = JSON.parse(request.responseText);
                var base_family_member = new_data.persons[1];
                if (!_.isEqual(data, new_data) && (base_family_member.name)) {
                    data = new_data;
                    self.draw_data(data);
                    self.expand_tree();
                }
            }
        }

        request.send()
    }

    expand_tree() {
        /* For each "Person" instance in the tree, simulate a click event to expand them. */
        var lastExpandableNodes = [];
        var nodesLeft = true;

        while(nodesLeft) {
            var expandableNodes = this.root.ft_datahandler.nodes
                .filter(n => !n.id.includes("u") && n.visible && n.is_root())
                .sort(function(a, b) { return a.id - b.id; })

            if (expandableNodes.length > 0 && !_.isEqual(expandableNodes, lastExpandableNodes)) {
                expandableNodes.forEach(c => c.click());
                lastExpandableNodes = expandableNodes;

                /* The tree should only be centred once when it is first rendered. */
                if (!this.treeCentred) {
                    /* Reset the position of the root of the tree to ensure that the tree is centred. */
                    var container = $("#family-tree-container");
                    var offset = container.offset();
                    var width = container.width();
                    var height = container.height();
                    this.root.x0 = offset.left + width / 2;
                    this.root.y0 = offset.top + height / 2;
                }

                /* Redraw the tree. */
                this.draw();
            } else {
                nodesLeft = false;
                this.treeCentred = true;
            }
        }
    }
};