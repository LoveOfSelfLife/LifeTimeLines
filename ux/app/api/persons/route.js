
import { headers } from 'next/headers'

export async function GET(request, response) {
    console.log('GET /api/persons:')
    const persons = [
        {
            "id": 1,
            "name": "John Doe",
            "age": 25,
            "home": "New York"
        },
        {
            "id": 2,
            "name": "Jane Doe",
            "age": 24,
            "home": "New York"
        },
        {
            "id": 3,
            "name": "John Smith",
            "age": 23,
            "home": "New Jersey"
        },
        {
            "id": 4,
            "name": "Jane Smith",
            "age": 27,
            "home": "Pennsylvania"
        }
    ]
    return Response.json( persons );
  };

  var idcounter = 5;

  export async function POST(request, response) {
    console.log("POST /api/persons");
    
    const data = await request.json();
    
    const URI = '/api/persons/' + idcounter++;
    console.log("POST /api/persons");
    console.log("location: " + URI);

    return new Response('Success!', {
        status: 201,
        headers: {
          'Content-Type': 'application/json',
          'location': URI
        }
      });
  }
