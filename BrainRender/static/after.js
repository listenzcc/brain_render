console.log("After js is running");

{
    const myCanvas = document.getElementById("canvas-1");
    const myContext = myCanvas.getContext("2d");

    const renderOptions = {
        x: 0,
        y: 0,
        z: 0,
        x2: 0,
        y2: 0,
        z2: 0,
        select: 10000,
        defaultSelect: 10000,
        atlas: "----",
        defaultAtlas: "----",
    };

    // Render the volume rendering
    const mkSrc = () => {
        renderOptions["x"] = document.getElementById("input-degree-x").value;
        renderOptions["y"] = document.getElementById("input-degree-y").value;
        renderOptions["z"] = document.getElementById("input-degree-z").value;

        const { x, y, z, x2, y2, z2, select } = renderOptions;

        const src = `./volumeRender?degX=${x}&degY=${y}&degZ=${z}&degX2=${x2}&degY2=${y2}&degZ2=${z2}&select=${select}`;
        return src;
    };

    function updateDoms() {
        const { atlas } = renderOptions;

        document.getElementById("h2-1").innerHTML = atlas;
    }

    function volumeRender(event) {
        var myImage = new Image();

        const src = mkSrc();

        myImage.src = src;

        myImage.onload = function (event) {
            const width = myCanvas.width,
                height = (myCanvas.width / myImage.width) * myImage.height;

            const x = 0,
                y =
                    height < myCanvas.height
                        ? (myCanvas.height - height) / 2
                        : 0;

            myContext.drawImage(myImage, x, y, width, height);
        };

        updateDoms();
    }

    // A proper initial and add event listener
    {
        volumeRender();
        for (let input of document.getElementsByClassName("DegreeInput")) {
            input.addEventListener("input", volumeRender);
        }
    }

    // Atlas table
    d3.json("./atlasTable").then((json) => {
        console.log(json);

        const data = [];
        const table = {};

        for (const i in json.name) {
            const name = json.name[i],
                x = json.x[i],
                y = json.y[i],
                z = json.z[i],
                idx = json.idx[i];
            data.push({ name, x, y, z, idx });
            table[name] = { idx, x, y, z };
        }

        const datalist = d3.select("#atlas-list-1");

        // Clear the datalist
        datalist.selectAll("option").data([]).exit().remove();

        // Append the datalist
        datalist
            .selectAll("option")
            .data(data)
            .enter()
            .append("option")
            .attr("value", (e) => e.name)
            .text((e) => {
                return e.idx;
            });

        const selector = d3.select("#atlas-selector-1");
        selector.on("change", (event) => {
            const value = table[event.target.value];

            renderOptions["select"] = value
                ? value.idx
                : renderOptions["defaultSelect"];

            renderOptions["atlas"] = value
                ? event.target.value
                : renderOptions["defaultAtlas"];

            volumeRender();
        });
    });

    // Canvas on drag
    {
        const dragOptions = {
            ondrag: false,
            x: 0,
            y: 0,
            dx: 0,
            dy: 0,
        };

        myCanvas.onmousedown = (e) => {
            dragOptions.ondrag = true;

            const { clientX, clientY } = e;

            dragOptions.x = clientX;
            dragOptions.y = clientY;
            dragOptions.dx = 0;
            dragOptions.dy = 0;

            renderOptions["x2"] = 0;
            renderOptions["y2"] = 0;
            renderOptions["z2"] = 0;
        };

        myCanvas.onmouseleave = (e) => {
            dragOptions.ondrag = false;

            dragOptions.dx = 0;
            dragOptions.dy = 0;

            renderOptions["x2"] = 0;
            renderOptions["y2"] = 0;
            renderOptions["z2"] = 0;
        };

        myCanvas.onmousemove = (e) => {
            if (dragOptions.ondrag) {
                const { clientX, clientY } = e;

                const dx = clientX - dragOptions.x,
                    dy = clientY - dragOptions.y;

                if (
                    Math.abs(dx - dragOptions.dx) > 50 ||
                    Math.abs(dy - dragOptions.dy) > 50
                ) {
                    // Mouse drag 100 pixels to flip 45 degrees
                    const scaler = d3
                        .scaleLinear()
                        .domain([0, 100])
                        .range([0, 45]);
                    const degX = scaler(dx),
                        degY = scaler(dy);

                    renderOptions["z2"] = degX;
                    renderOptions["y2"] = -degY;

                    console.log({ dx, dy, degX, degY });

                    dragOptions.dx = dx;
                    dragOptions.dy = dy;

                    volumeRender();
                }
            }
        };

        myCanvas.onmouseup = (e) => {
            dragOptions.ondrag = false;

            dragOptions.dx = 0;
            dragOptions.dy = 0;

            renderOptions["x2"] = 0;
            renderOptions["y2"] = 0;
            renderOptions["z2"] = 0;
        };
    }
}

console.log("After js finishes");
