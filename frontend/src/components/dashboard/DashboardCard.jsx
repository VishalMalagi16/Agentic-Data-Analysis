// frontend/components/dashboard/DashboardCard.jsx

const CardContent = ({ card }) => {
    switch (card.type) {
      case 'plot':
        return (
          <div className="p-4 bg-gray-50 rounded-b-lg">
            <img
              src={`http://127.0.0.1:8000${card.path}`} // Connects to your FastAPI static files
              alt={card.title || 'Analysis Plot'}
              className="w-full h-auto rounded-md border border-gray-200"
            />
          </div>
        );
      case 'stat':
        return (
          <div className="p-4">
            <p className="text-4xl font-bold text-blue-600">{card.value}</p>
          </div>
        );
      // Add more cases for tables, etc.
      default:
        return null;
    }
  };
  
  export const DashboardCard = ({ card }) => {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-bold text-gray-800">{card.title}</h3>
          {card.summary && <p className="text-sm text-gray-600 mt-1">{card.summary}</p>}
        </div>
        <CardContent card={card} />
      </div>
    );
  };