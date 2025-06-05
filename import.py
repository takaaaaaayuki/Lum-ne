from akijyoukyou import akijyoukyou_bp
from app import app

# Blueprint を `app` に登録
app.register_blueprint(akijyoukyou_bp)
