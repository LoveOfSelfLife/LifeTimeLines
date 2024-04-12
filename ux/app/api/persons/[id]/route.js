
export async function GET( request, { params} ) {
    const id = params.id;
    const person = {
        "id": "2",
        "name": "Jane Doe",
        "age": 24,
        "home": "New York"
    };
    return Response.json( person )
  }

  export async function PUT(request, { params }, response) {
    console.log("PUT /api/persons/:id")
    return new Response('Success!', {
        status: 200,
      })    
  }

  export async function DELETE(request, { params },  response) {
    console.log("DELETE /api/persons/:id")
    return new Response('Success!', {
        status: 200,
      });
  }
