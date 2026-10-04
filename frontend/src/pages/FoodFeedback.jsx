import React, { useState, useEffect } from 'react';
import { Star, MessageSquare, TrendingUp, TrendingDown, AlertCircle, CheckCircle2, Info } from 'lucide-react';
import { foodService } from '../services/foodService';

export default function FoodFeedback() {
  const [items, setItems] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [responseText, setResponseText] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const fItems = await foodService.getFoodItems();
    const allRev = await foodService.getAllReviews();
    setItems(fItems.sort((a,b) => (b.reviewCount || 0) - (a.reviewCount || 0)));
    setReviews(allRev);
    setLoading(false);
  };

  const handleResponseSubmit = async (reviewId) => {
    const text = responseText[reviewId];
    if (!text) return;
    try {
      await foodService.updateManagerResponse(reviewId, text);
      setResponseText({ ...responseText, [reviewId]: '' });
      loadData(); // reload
    } catch (err) {
      console.error(err);
    }
  };

  const renderInsights = (item) => {
    if (!item.rating) return null;
    let recommendation = "";
    let color = "text-secondary";
    let icon = <Info size={16}/>;

    if (item.rating >= 4.5 && item.reviewCount > 10) {
      recommendation = "High demand & high satisfaction. Promote this item.";
      color = "text-success";
      icon = <TrendingUp size={16}/>;
    } else if (item.rating < 3.5 && item.reviewCount > 5) {
      recommendation = "Low rating. Consider improving recipe, price or presentation.";
      color = "text-danger";
      icon = <TrendingDown size={16}/>;
    } else {
      recommendation = "Performing adequately. Monitor for trends.";
    }

    return (
      <div className={`mt-2 text-sm flex items-start gap-2 ${color}`}>
        {icon} <span>{recommendation}</span>
      </div>
    );
  };

  if (loading) return <div className="p-8 text-center">Loading feedback data...</div>;

  const displayReviews = selectedItem 
    ? reviews.filter(r => r.foodItemId === selectedItem.id)
    : reviews;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Food Feedback & Insights</h1>
          <p className="text-secondary">Analyze customer satisfaction and optimize your menu.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col: Food Items Performance */}
        <div className="lg:col-span-1 card">
          <h3 className="section-title mb-4">Menu Performance</h3>
          <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
            <div 
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${!selectedItem ? 'border-primary bg-primary-light bg-opacity-10' : 'hover:bg-background'}`}
              onClick={() => setSelectedItem(null)}
            >
              <div className="font-bold text-primary">All Reviews</div>
              <div className="text-sm text-secondary">{reviews.length} total reviews</div>
            </div>
            {items.filter(i => i.reviewCount > 0).map(item => (
              <div 
                key={item.id} 
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${selectedItem?.id === item.id ? 'border-primary bg-primary-light bg-opacity-10' : 'hover:bg-background'}`}
                onClick={() => setSelectedItem(item)}
              >
                <div className="flex justify-between items-start">
                  <div className="font-bold">{item.name}</div>
                  <div className="flex items-center text-sm font-bold text-warning">
                    <Star size={14} fill="currentColor" className="mr-1"/> {item.rating.toFixed(1)}
                  </div>
                </div>
                <div className="text-sm text-secondary mt-1">{item.reviewCount} Reviews</div>
                {item.rating < 3.5 && (
                  <div className="text-xs text-danger mt-1 flex items-center">
                    <AlertCircle size={12} className="mr-1"/> Needs Attention
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Right Col: Reviews & Responses */}
        <div className="lg:col-span-2 space-y-6">
          
          {selectedItem && (
            <div className="card bg-background border border-primary">
              <h3 className="section-title text-primary">Menu Insight</h3>
              <div className="flex justify-between items-center mt-2">
                <div>
                  <h4 className="text-lg font-bold">{selectedItem.name}</h4>
                  <div className="flex items-center text-warning font-bold mt-1">
                    <Star size={16} fill="currentColor" className="mr-1"/> {selectedItem.rating.toFixed(1)} 
                    <span className="text-secondary font-normal text-sm ml-2">({selectedItem.reviewCount} reviews)</span>
                  </div>
                </div>
                <button className="btn btn-outline" onClick={() => window.location.href='/inventory'}>EDIT FOOD</button>
              </div>
              <div className="mt-4 pt-4 border-t border-border">
                <strong className="text-sm uppercase text-secondary block mb-1">Recommendation</strong>
                {renderInsights(selectedItem) || "No insights available yet."}
              </div>
            </div>
          )}

          <div className="card">
            <h3 className="section-title mb-4">
              {selectedItem ? `Customer Reviews for ${selectedItem.name}` : 'Recent Customer Reviews'}
            </h3>
            
            {displayReviews.length === 0 ? (
              <div className="text-center p-8 text-secondary border border-dashed rounded-lg">
                No reviews found.
              </div>
            ) : (
              <div className="space-y-4">
                {displayReviews.map(review => {
                  const food = items.find(i => i.id === review.foodItemId);
                  return (
                    <div key={review.id} className="border rounded-lg p-4 bg-background">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-bold">{review.userName}</div>
                          {!selectedItem && <div className="text-xs text-primary font-bold mt-1">Item: {food?.name}</div>}
                          <div className="text-xs text-success flex items-center mt-1">
                            <CheckCircle2 size={12} className="mr-1"/> Verified Order
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-secondary mb-1">{new Date(review.createdAt).toLocaleDateString()}</div>
                          <div className="flex">
                            {[...Array(5)].map((_, i) => (
                              <Star key={i} size={14} fill={i < review.rating ? 'var(--warning)' : 'none'} color={i < review.rating ? 'var(--warning)' : 'var(--border)'} />
                            ))}
                          </div>
                        </div>
                      </div>
                      
                      <p className="text-sm mt-3 mb-4 text-dark">{review.comment || 'No comment provided.'}</p>
                      
                      {review.managerResponse ? (
                        <div className="bg-surface p-3 rounded border-l-2 border-primary text-sm">
                          <strong className="text-xs uppercase text-secondary block mb-1">Your Response</strong>
                          {review.managerResponse}
                        </div>
                      ) : (
                        <div className="mt-2 flex gap-2">
                          <input 
                            type="text" 
                            className="input-field flex-1 text-sm" 
                            placeholder="Write a response to the customer..."
                            value={responseText[review.id] || ''}
                            onChange={(e) => setResponseText({...responseText, [review.id]: e.target.value})}
                          />
                          <button 
                            className="btn btn-primary text-sm"
                            onClick={() => handleResponseSubmit(review.id)}
                            disabled={!responseText[review.id]}
                          >
                            Reply
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
