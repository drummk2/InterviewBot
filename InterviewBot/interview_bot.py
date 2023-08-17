from data.mappers.db_to_json_mapper import DBToJSONMapper
from flask import Flask, render_template, url_for

interview_bot = Flask(
  __name__,
  template_folder = './wwwroot/templates',
  static_folder = './wwwroot/static')

@interview_bot.route('/get_family_tree_representation', methods = ['GET'])
def get_family_tree_representation() -> str:
    return DBToJSONMapper().get_current_tree_representation()

@interview_bot.route('/', methods = ['GET'])
def index():
    return render_template(
        'index.html',
        family_tree_data_url = url_for('get_family_tree_representation'),
        initial_tree_representation = DBToJSONMapper().get_current_tree_representation())

if __name__ == '__main__':
    interview_bot.run(debug = True)