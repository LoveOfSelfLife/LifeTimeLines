
export async function GET( request, { params} ) {
    const id = params.id;
    // const res = await fetch('https://jsonplaceholder.typicode.com/todos' + '/' + id, {
    // const res = await fetch('https://data.mongodb-api.com/...', {
    //   headers: {
        // 'Content-Type': 'application/json',
        // 'API-Key': process.env.DATA_API_KEY,
    //   },
    // })
    // const data = await res.json()
    const person = {
        "id": "2",
        "name": "Jane Doe",
        "age": 24,
        "home": "New York"
    };
    // console.log(request);    
    return Response.json( person )
  }

  export async function PUT(request, { params }, response) {
    console.log("PUT /api/persons/:id")
    // const id = params.id;
    // console.log("ID:");
    // console.log(id);
    // const data = await request.json();

    // console.log("REQUEST DATA: ");
    // console.log(data);

    return new Response('Success!', {
        status: 200,
      })    
  }

  export async function DELETE(request, { params },  response) {
    console.log("DELETE /api/persons/:id")
    // console.log(request);
    // const id = params.id;
    // console.log("ID:");
    // console.log(id);

    // const data = await request.json();

    // console.log("REQUEST DATA: ");
    // console.log(data);

    return new Response('Success!', {
        status: 200,
      });
  }
