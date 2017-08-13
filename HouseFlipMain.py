from flask import Flask,render_template,request
import scraper
app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html',listings=[])

@app.route('/search',methods=['POST','GET'])
def result():
	min_price = request.args.get('min_price')
	max_price = request.args.get('max_price')
	city = request.args.get('city')
	state = request.args.get('state')
	listings = scraper.results(city,state,min_price,max_price)
	return render_template('index.html',listings=listings)









if  __name__=='__main__':
	app.run(debug=True)
